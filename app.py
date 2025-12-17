import subprocess
import sys
import importlib.util
import os

# -------------------------------------------------------
# PACKAGE INSTALLER
# -------------------------------------------------------
# Map: 'import_name': 'pip_package_name'
required_packages = {
    'flask': 'Flask',
    'langchain_text_splitters': 'langchain-text-splitters',
    # Note: langchain-text-splitters usually installs langchain-core automatically
}

def install_and_import(import_name, pip_name):
    # check if module is already installed
    if importlib.util.find_spec(import_name) is None:
        print(f"📦 [System]: Installing {pip_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
            print(f"✅ [System]: {pip_name} installed successfully.")
        except subprocess.CalledProcessError:
            print(f"❌ [System]: Failed to install {pip_name}. Check internet connection.")
            sys.exit(1)
    else:
        print(f"🔹 [System]: {pip_name} is already installed.")

print("---------------------------------------")
print("   Initializing ChunkFlow Environment  ")
print("---------------------------------------")
for import_name, install_name in required_packages.items():
    install_and_import(import_name, install_name)
print("---------------------------------------\n")

# -------------------------------------------------------
# APP IMPORTS & LOGIC
# -------------------------------------------------------
import shutil
import json
import re
import uuid
import zipfile
from flask import Flask, render_template, request, send_file, jsonify

# LangChain imports (now guaranteed to exist)
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
OUTPUT_FOLDER = 'temp_outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --- Helper Functions ---

def clean_gemini_markdown(text):
    """Removes code block wrappers often added by LLMs"""
    text = re.sub(r'^```markdown\s*', '', text) 
    text = re.sub(r'^```\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    return text.strip()

def process_files(file_paths, chunk_size, chunk_overlap, session_id):
    """Core logic to split MD files and zip them"""
    
    # 1. Setup session directory
    session_dir = os.path.join(OUTPUT_FOLDER, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    # 2. Configure Splitters
    # First: Structure aware splitting
    headers_to_split_on = [
        ("#", "H1"),
        ("##", "H2"),
        ("###", "H3"),
    ]
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, 
        strip_headers=False
    )

    # Second: Size enforcement
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap
    )

    logs = []
    
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        file_base_name = os.path.splitext(file_name)[0]
        
        try:
            # Folder for this specific document
            doc_folder = os.path.join(session_dir, file_base_name)
            os.makedirs(doc_folder, exist_ok=True)
            
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()

            # Clean & Split
            clean_text = clean_gemini_markdown(raw_text)
            header_splits = md_splitter.split_text(clean_text)
            final_chunks = text_splitter.split_documents(header_splits)

            # Save Chunks
            for i, chunk in enumerate(final_chunks):
                chunk_data = {
                    "source": file_name,
                    "chunk_index": i,
                    "metadata": chunk.metadata,
                    "content": chunk.page_content
                }
                
                # Naming: docname_part_001.json
                chunk_filename = f"{file_base_name}_part_{i+1:03d}.json"
                save_path = os.path.join(doc_folder, chunk_filename)
                
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(chunk_data, f, indent=2, ensure_ascii=False)
            
            logs.append({"file": file_name, "status": "success", "chunks": len(final_chunks)})

        except Exception as e:
            logs.append({"file": file_name, "status": "error", "message": str(e)})

    # 3. Zip the result
    zip_filename = f"chunks_{session_id}"
    zip_path_no_ext = os.path.join(OUTPUT_FOLDER, zip_filename)
    shutil.make_archive(zip_path_no_ext, 'zip', session_dir)
    
    # 4. Cleanup unzipped session data
    shutil.rmtree(session_dir)
    
    return f"{zip_filename}.zip", logs

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    # Generate unique ID for this processing batch
    session_id = str(uuid.uuid4())
    
    uploaded_files = request.files.getlist('files')
    
    # Get form data or use defaults
    try:
        chunk_size = int(request.form.get('chunk_size', 4000))
        chunk_overlap = int(request.form.get('chunk_overlap', 400))
    except ValueError:
        chunk_size = 4000
        chunk_overlap = 400
    
    if not uploaded_files or uploaded_files[0].filename == '':
        return jsonify({'error': 'No files uploaded'}), 400

    saved_paths = []
    try:
        # Save uploads temporarily
        for file in uploaded_files:
            if file.filename.endswith('.md'):
                # Prefix filename with session_id to prevent collisions in temp folder
                safe_name = f"{session_id}_{file.filename}"
                path = os.path.join(UPLOAD_FOLDER, safe_name)
                file.save(path)
                saved_paths.append(path)
        
        if not saved_paths:
            return jsonify({'error': 'No Valid .md files found'}), 400

        # Run Logic
        zip_name, logs = process_files(saved_paths, chunk_size, chunk_overlap, session_id)
        
        # Cleanup Input Files
        for p in saved_paths:
            if os.path.exists(p):
                os.remove(p)
            
        return jsonify({
            'download_url': f"/download/{zip_name}",
            'logs': logs
        })

    except Exception as e:
        # Clean up if everything explodes
        for p in saved_paths:
            if os.path.exists(p):
                os.remove(p)
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    # Sanitize filename to prevent directory traversal
    safe_name = os.path.basename(filename)
    return send_file(os.path.join(OUTPUT_FOLDER, safe_name), as_attachment=True)

if __name__ == '__main__':
    # Listen on all interfaces for Docker/Tunnel compatibility
    print("🚀 ChunkFlow is running on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)