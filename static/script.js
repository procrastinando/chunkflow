document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const fileListDisplay = document.getElementById('file-list-display');
    const convertBtn = document.getElementById('convert-btn');
    
    // Steps
    const step1 = document.getElementById('step-1');
    const step2 = document.getElementById('step-2');
    const step3 = document.getElementById('step-3');

    // State
    let selectedFiles = [];

    // Handle File Selection
    fileInput.addEventListener('change', (e) => {
        selectedFiles = Array.from(e.target.files);
        if (selectedFiles.length > 0) {
            fileListDisplay.innerHTML = `<i class="fa-solid fa-check"></i> ${selectedFiles.length} file(s) ready`;
            convertBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> Process ${selectedFiles.length} Files`;
        } else {
            fileListDisplay.innerHTML = '';
            convertBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> Process Files`;
        }
    });

    // Handle Processing
    convertBtn.addEventListener('click', async () => {
        if (selectedFiles.length === 0) {
            alert("Please upload at least one .md file");
            return;
        }

        // Switch to Processing View
        step1.classList.remove('active');
        step2.classList.add('active');

        const formData = new FormData();
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('chunk_size', document.getElementById('chunk-size').value);
        formData.append('chunk_overlap', document.getElementById('chunk-overlap').value);

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Processing failed');
            }

            // Success - Switch to Step 3
            showResults(data);

        } catch (error) {
            alert("Error: " + error.message);
            location.reload();
        }
    });

    function showResults(data) {
        step2.classList.remove('active');
        step3.classList.add('active');

        // Setup Download
        const downloadBtn = document.getElementById('download-btn');
        downloadBtn.href = data.download_url;

        // Populate Logs
        const logContainer = document.getElementById('log-container');
        logContainer.innerHTML = ''; 

        let totalChunks = 0;

        data.logs.forEach(log => {
            if(log.status === 'success') {
                totalChunks += log.chunks;
                logContainer.innerHTML += `
                <div class="task-item done">
                    <div class="task-icon"><i class="fa-solid fa-file-code"></i></div>
                    <div class="task-info">
                        <div class="task-header">${log.file}</div>
                        <div class="task-detail">Created ${log.chunks} chunks</div>
                    </div>
                </div>`;
            } else {
                logContainer.innerHTML += `
                <div class="task-item" style="border-color: #ef4444;">
                    <div class="task-icon" style="color: #ef4444;"><i class="fa-solid fa-triangle-exclamation"></i></div>
                    <div class="task-info">
                        <div class="task-header">${log.file}</div>
                        <div class="task-detail">Error: ${log.message}</div>
                    </div>
                </div>`;
            }
        });

        document.getElementById('result-stats').innerText = `Total ${totalChunks} chunks generated.`;
        
        // History Mockup
        const historyList = document.getElementById('history-list');
        const historyItem = document.createElement('li');
        historyItem.innerHTML = `
            <span>Batch Process (${selectedFiles.length} files)</span>
            <a href="${data.download_url}" class="history-link">DL</a>
        `;
        if(historyList.children[0].innerText.includes("No recent")) historyList.innerHTML = '';
        historyList.prepend(historyItem);
    }
});