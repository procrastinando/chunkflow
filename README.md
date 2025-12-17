# ChunkFlow
Precision Markdown Splitting for RAG Pipelines.

ChunkFlow is a self-hosted web application that intelligently processes Markdown files into structured, semantic chunks. It is designed specifically to bridge the gap between raw documentation and Vector Databases (Pinecone, Milvus, Weaviate) for high-quality RAG (Retrieval-Augmented Generation).

Unlike simple character splitters, ChunkFlow respects the document structure, ensuring headers and sections remain intact before enforcing token limits.

**Powered by Flask, LangChain, and Docker.**

## Features
*   **Hybrid Splitting Engine**: First splits by Markdown Headers (H1-H3) to preserve context, then splits by character count to fit embedding models (e.g., BGE-M3).
*   **Granular Output**: Generates individual JSON files per chunk (`doc_part_001.json`) containing metadata and content, zipped for easy download.
*   **Gemini/LLM Cleanup**: Automatically detects and removes ` ```markdown ` wrappers often hallucinated by LLMs during markdown generation.
*   **Concurrency Safe**: Uses session-based UUIDs to allow multiple users or tabs to process files simultaneously without data collision.
*   **Runtime Dependency Management**: No complex build steps. The app self-configures its environment on the first run.

## Getting Started

### Prerequisites
*   Docker & Docker Compose

### Method 1: Docker Compose (Recommended)
1. Clone the repository or create the folder structure.
2. Start the container:
   ```bash
   docker compose up -d --build
   ```
3. Access the UI: Open your browser and go to `http://localhost:5000`.

### Method 2: Manual Docker Build
If you prefer running without Compose:

```bash
# 1. Build the image
docker build -t chunkflow .

# 2. Run the container
# Runs on port 5000. No volume mounting strictly required as data is transient.
docker run -d \
  -p 5000:5000 \
  --name chunkflow \
  chunkflow
```

## Usage Guide

### 1. The Strategy
ChunkFlow uses a "Structure First, Size Second" approach:
1.  **Header Split**: The document is divided by `#`, `##`, and `###`. This ensures a chunk never starts in the middle of a paragraph from a previous section.
2.  **Recursive Split**: If a specific section is larger than your defined **Chunk Size** (default 4000 chars), it is further split recursively with overlap.

### 2. Output Format
The tool produces a `.zip` file containing a folder for each uploaded document.

**Example Input**: `Project_Documentation.md`

**Example Output (Inside JSON)**:
```json
{
  "source": "Project_Documentation.md",
  "chunk_index": 0,
  "metadata": {
    "Header 1": "Installation",
    "Header 2": "Docker"
  },
  "content": "Step 1: Run docker compose up..."
}
```

## Configuration

### Adjustable Parameters (UI)
*   **Chunk Size**: The maximum number of characters per chunk. Default is `4000` (roughly 1000 tokens, ideal for `bge-m3` or `text-embedding-3-large`).
*   **Overlap**: The number of characters to overlap between chunks to maintain semantic continuity.

### Deployment Behind Proxy
The application listens on `0.0.0.0:5000`. It is ready to be placed behind a Cloudflare Tunnel or Nginx Reverse Proxy. No additional configuration is required.

## Tech Stack
*   **Backend**: Python 3.11, Flask.
*   **Logic**: LangChain Text Splitters.
*   **Frontend**: HTML5, CSS3, Vanilla JS.