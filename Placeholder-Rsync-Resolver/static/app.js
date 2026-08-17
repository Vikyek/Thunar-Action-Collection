document.addEventListener("DOMContentLoaded", () => {
    // Inputs
    const srcInput = document.getElementById("src-input");
    const actualInput = document.getElementById("actual-input");
    const destInput = document.getElementById("dest-input");
    const checkForceAll = document.getElementById("check-force-all");
    
    // Buttons
    const btnScan = document.getElementById("btn-scan");
    const btnResolve = document.getElementById("btn-resolve");
    const btnClearLogs = document.getElementById("btn-clear-logs");
    
    // DOM Layout Elements
    const statusBar = document.getElementById("status-bar");
    const itemsCounter = document.getElementById("items-counter");
    const treeContainer = document.getElementById("tree-container");
    const listPlaceholders = document.getElementById("list-placeholders");
    const listFull = document.getElementById("list-full");
    const sectionPlaceholders = document.getElementById("section-placeholders");
    const sectionFull = document.getElementById("section-full");
    const consoleLogs = document.getElementById("console-logs");
    
    // Modal Elements
    const modalBackdrop = document.getElementById("confirm-modal");
    const modalClose = document.getElementById("modal-close");
    const btnModalCancel = document.getElementById("btn-modal-cancel");
    const btnModalConfirm = document.getElementById("btn-modal-confirm");
    
    const confirmActionName = document.getElementById("confirm-action-name");
    const modalCountPlaceholders = document.getElementById("modal-count-placeholders");
    const modalCountFull = document.getElementById("modal-count-full");

    // Local state
    let scanResults = {
        placeholders: [],
        local_full: []
    };

    // Clear logs button
    btnClearLogs.addEventListener("click", () => {
        consoleLogs.innerHTML = '<div class="console-placeholder">Waiting for process start...</div>';
    });

    // Scan directory button
    btnScan.addEventListener("click", async () => {
        const src = srcInput.value.trim();
        const actual = actualInput.value.trim();
        const dest = destInput.value.trim();
        
        if (!src) {
            updateStatus("Error: Placeholder source directory is required.", true);
            return;
        }

        btnScan.disabled = true;
        btnScan.textContent = "Scanning...";
        updateStatus("Scanning placeholder directory...");
        
        try {
            const response = await fetch("/api/scan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    src_dir: src,
                    actual_source: actual,
                    dest_dir: dest,
                    force_all: checkForceAll.checked
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                scanResults = data;
                renderScanResults(data);
            } else {
                showErrorState(data.error || "Failed to scan folder.");
            }
        } catch (err) {
            showErrorState("Network error: Failed to connect to local server.");
        } finally {
            btnScan.disabled = false;
            btnScan.textContent = "Scan Folder";
        }
    });

    // Resolve button opens modal
    btnResolve.addEventListener("click", () => {
        const totalItems = scanResults.placeholders.length + scanResults.local_full.length;
        if (totalItems === 0) return;
        
        const action = document.querySelector('input[name="action-mode"]:checked').value;
        const actual = actualInput.value.trim();
        const dest = destInput.value.trim();
        
        if (!actual) {
            updateStatus("Error: Please specify the actual source (local path or remote like user@host:path).", true);
            actualInput.focus();
            return;
        }
        if (!dest) {
            updateStatus("Error: Please specify the destination directory path.", true);
            destInput.focus();
            return;
        }

        // Setup modal state
        confirmActionName.textContent = action;
        modalCountPlaceholders.textContent = scanResults.placeholders.length;
        modalCountFull.textContent = scanResults.local_full.length;
        
        // Show modal
        modalBackdrop.style.display = "flex";
    });

    // Close modal triggers
    const closeModal = () => {
        modalBackdrop.style.display = "none";
    };
    modalClose.addEventListener("click", closeModal);
    btnModalCancel.addEventListener("click", closeModal);
    modalBackdrop.addEventListener("click", (e) => {
        if (e.target === modalBackdrop) closeModal();
    });

    // Confirm & Start stream!
    btnModalConfirm.addEventListener("click", () => {
        closeModal();
        
        const src = srcInput.value.trim();
        const actual = actualInput.value.trim();
        const dest = destInput.value.trim();
        const action = document.querySelector('input[name="action-mode"]:checked').value;
        
        // Disable actions
        btnResolve.disabled = true;
        btnScan.disabled = true;
        
        // Clear terminal logs
        consoleLogs.innerHTML = "";
        
        // Build SSE URL
        const params = new URLSearchParams({
            src: src,
            actual: actual,
            dest: dest,
            action: action,
            force_all: checkForceAll.checked
        });
        
        updateStatus("Initializing rsync pipeline...");
        
        // Establish EventSource stream
        const eventSource = new EventSource(`/api/resolve/stream?${params.toString()}`);
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.event === "start") {
                updateStatus(data.message);
                appendLogLine(data.message, "cmd");
            } else if (data.event === "log") {
                appendLogLine(data.message);
                
                // Keep status bar updated with transfer events
                if (data.message.startsWith("[Local Copy]") || data.message.startsWith("[Rsync]")) {
                    updateStatus(data.message);
                }
            } else if (data.event === "done") {
                updateStatus(data.message);
                appendLogLine(data.message, "success");
                eventSource.close();
                
                // Re-enable actions
                btnScan.disabled = false;
                // Re-scan directory to update items list
                btnScan.click();
            } else if (data.event === "error") {
                updateStatus(data.message, true);
                appendLogLine(data.message, "error");
                eventSource.close();
                
                btnScan.disabled = false;
                btnResolve.disabled = false;
            }
        };
        
        eventSource.onerror = () => {
            updateStatus("Error: Lost connection to resolution stream.", true);
            appendLogLine("[Error] Server-Sent Events stream connection lost.", "error");
            eventSource.close();
            
            btnScan.disabled = false;
            btnResolve.disabled = false;
        };
    });

    function renderScanResults(data) {
        const totalPlaceholders = data.placeholders.length;
        const totalFull = data.local_full.length;
        const totalItems = totalPlaceholders + totalFull;
        
        itemsCounter.textContent = `${totalItems} file${totalItems === 1 ? "" : "s"} found`;
        
        listPlaceholders.innerHTML = "";
        listFull.innerHTML = "";
        
        if (totalItems === 0) {
            showEmptyState();
            btnResolve.disabled = true;
            updateStatus("Scan complete. No files found to resolve.");
            return;
        }
        
        // Display lists
        treeContainer.classList.remove("empty");
        treeContainer.querySelector(".empty-state").style.display = "none";
        treeContainer.querySelector(".scan-lists").style.display = "block";
        
        if (totalPlaceholders > 0) {
            sectionPlaceholders.style.display = "block";
            data.placeholders.forEach(file => {
                const li = document.createElement("li");
                li.textContent = file;
                listPlaceholders.appendChild(li);
            });
        } else {
            sectionPlaceholders.style.display = "none";
        }
        
        if (totalFull > 0) {
            sectionFull.style.display = "block";
            data.local_full.forEach(file => {
                const li = document.createElement("li");
                li.textContent = file;
                listFull.appendChild(li);
            });
        } else {
            sectionFull.style.display = "none";
        }
        
        btnResolve.disabled = false;
        updateStatus(`Scan complete. Found ${totalPlaceholders} placeholders to download, ${totalFull} local files ready.`);
    }

    function showEmptyState() {
        treeContainer.classList.add("empty");
        treeContainer.querySelector(".empty-state").style.display = "flex";
        treeContainer.querySelector(".scan-lists").style.display = "none";
        
        // Reset defaults
        const emptyState = treeContainer.querySelector(".empty-state");
        emptyState.querySelector(".empty-icon").textContent = "📁";
        emptyState.querySelector("h3").textContent = "No files scanned yet";
        emptyState.querySelector("p").textContent = 'Configure paths on the left and click "Scan Folder" to display identified files.';
    }

    function showErrorState(errMessage) {
        scanResults = { placeholders: [], local_full: [] };
        listPlaceholders.innerHTML = "";
        listFull.innerHTML = "";
        itemsCounter.textContent = "0 files found";
        btnResolve.disabled = true;
        
        treeContainer.classList.add("empty");
        const emptyState = treeContainer.querySelector(".empty-state");
        emptyState.style.display = "flex";
        emptyState.querySelector(".empty-icon").textContent = "⚠️";
        emptyState.querySelector("h3").textContent = "Scan Failed";
        emptyState.querySelector("p").textContent = errMessage;
        
        treeContainer.querySelector(".scan-lists").style.display = "none";
        updateStatus("Error: " + errMessage, true);
    }

    function appendLogLine(message, type = "") {
        const div = document.createElement("div");
        div.className = "log-line " + type;
        div.textContent = message;
        consoleLogs.appendChild(div);
        consoleLogs.scrollTop = consoleLogs.scrollHeight;
    }

    function updateStatus(message, isError = false) {
        statusBar.textContent = message;
        if (isError) {
            statusBar.style.color = "var(--color-danger)";
        } else {
            statusBar.style.color = "var(--text-muted)";
        }
    }
});
