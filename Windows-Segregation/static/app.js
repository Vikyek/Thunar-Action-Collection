document.addEventListener("DOMContentLoaded", () => {
    // Elements
    const dirInput = document.getElementById("dir-input");
    const btnReset = document.getElementById("btn-current-dir");
    const btnScan = document.getElementById("btn-scan");
    const btnSegregate = document.getElementById("btn-segregate");
    const checkBinaries = document.getElementById("check-binaries");
    
    const statusBar = document.getElementById("status-bar");
    const resultsContainer = document.getElementById("results-container");
    const resultsCounter = document.getElementById("results-counter");
    
    const listDirs = document.getElementById("list-dirs");
    const listFiles = document.getElementById("list-files");
    const sectionDirs = document.getElementById("section-dirs");
    const sectionFiles = document.getElementById("section-files");
    
    // Modal Elements
    const modalBackdrop = document.getElementById("confirm-modal");
    const btnModalCancel = document.getElementById("btn-modal-cancel");
    const btnModalConfirm = document.getElementById("btn-modal-confirm");
    const modalCloseX = document.getElementById("modal-close-x");
    const modalCountDirs = document.getElementById("modal-count-dirs");
    const modalCountFiles = document.getElementById("modal-count-files");
    
    // Default directory stored from render
    const defaultDir = dirInput.value;
    
    // Scanned data state
    let lastScanData = {
        success: false,
        directory: "",
        directories: [],
        files: []
    };

    // Reset button
    btnReset.addEventListener("click", () => {
        dirInput.value = defaultDir;
        updateStatus("Reset directory path");
    });

    // Scan button click handler
    btnScan.addEventListener("click", async () => {
        const path = dirInput.value.trim();
        if (!path) {
            updateStatus("Error: Directory path cannot be empty", true);
            return;
        }

        btnScan.disabled = true;
        btnScan.textContent = "Scanning...";
        updateStatus("Scanning filesystem...");
        
        try {
            const response = await fetch("/api/scan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    directory: path,
                    include_binaries: checkBinaries.checked
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                lastScanData = data;
                renderScanResults(data);
            } else {
                renderError(data.error || "An error occurred during scanning");
            }
        } catch (err) {
            renderError("Network error: Failed to connect to server");
        } finally {
            btnScan.disabled = false;
            btnScan.textContent = "Scan Directory";
        }
    });

    // Segregate click opens the modal
    btnSegregate.addEventListener("click", () => {
        const totalItems = lastScanData.directories.length + lastScanData.files.length;
        if (totalItems === 0) return;
        
        // Update modal values
        modalCountDirs.textContent = lastScanData.directories.length;
        modalCountFiles.textContent = lastScanData.files.length;
        
        // Show modal
        modalBackdrop.style.display = "flex";
    });

    // Close modal handlers
    const closeModal = () => {
        modalBackdrop.style.display = "none";
    };
    btnModalCancel.addEventListener("click", closeModal);
    modalCloseX.addEventListener("click", closeModal);
    
    // Close modal when clicking backdrop
    modalBackdrop.addEventListener("click", (e) => {
        if (e.target === modalBackdrop) closeModal();
    });

    // Confirm migration in modal
    btnModalConfirm.addEventListener("click", async () => {
        closeModal();
        
        btnSegregate.disabled = true;
        btnScan.disabled = true;
        updateStatus("Segregating files...");
        
        try {
            const response = await fetch("/api/segregate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    directory: lastScanData.directory,
                    include_binaries: checkBinaries.checked
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const results = data.results;
                const movedDirs = results.moved_directories.length;
                const movedFiles = results.moved_files.length;
                const errors = results.errors.length;
                
                let msg = `Successfully segregated: moved ${movedDirs} folders and ${movedFiles} files.`;
                if (errors > 0) {
                    msg += ` Failed to move ${errors} items.`;
                }
                
                updateStatus(msg);
                
                // Clear state and results panel
                clearResults();
                
                // Trigger a re-scan to show fresh directory state
                btnScan.click();
            } else {
                updateStatus("Error: " + (data.error || "Failed to segregate"), true);
                btnSegregate.disabled = false;
            }
        } catch (err) {
            updateStatus("Error: Failed to communicate with segregation endpoint", true);
            btnSegregate.disabled = false;
        } finally {
            btnScan.disabled = false;
        }
    });

    // Render results in tree view
    function renderScanResults(data) {
        const totalDirs = data.directories.length;
        const totalFiles = data.files.length;
        const totalItems = totalDirs + totalFiles;
        
        resultsCounter.textContent = `${totalItems} item${totalItems === 1 ? "" : "s"} found`;
        
        // Clear list containers
        listDirs.innerHTML = "";
        listFiles.innerHTML = "";
        
        if (totalItems === 0) {
            resultsContainer.classList.add("empty");
            resultsContainer.querySelector(".empty-state").style.display = "flex";
            resultsContainer.querySelector(".results-list").style.display = "none";
            
            btnSegregate.disabled = true;
            updateStatus("Scan complete. No Windows-specific items found.");
            return;
        }
        
        // Hide empty state and show list container
        resultsContainer.classList.remove("empty");
        resultsContainer.querySelector(".empty-state").style.display = "none";
        resultsContainer.querySelector(".results-list").style.display = "block";
        
        // Populate Directories
        if (totalDirs > 0) {
            sectionDirs.style.display = "block";
            data.directories.forEach(dir => {
                const li = document.createElement("li");
                li.textContent = dir;
                listDirs.appendChild(li);
            });
        } else {
            sectionDirs.style.display = "none";
        }
        
        // Populate Files
        if (totalFiles > 0) {
            sectionFiles.style.display = "block";
            data.files.forEach(file => {
                const li = document.createElement("li");
                li.textContent = file;
                listFiles.appendChild(li);
            });
        } else {
            sectionFiles.style.display = "none";
        }
        
        btnSegregate.disabled = false;
        updateStatus(`Found ${totalDirs} folder${totalDirs === 1 ? "" : "s"} and ${totalFiles} file${totalFiles === 1 ? "" : "s"}. Ready to segregate.`);
    }

    function renderError(errMessage) {
        clearResults();
        updateStatus("Error: " + errMessage, true);
        
        resultsContainer.classList.add("empty");
        const emptyState = resultsContainer.querySelector(".empty-state");
        emptyState.style.display = "flex";
        emptyState.querySelector(".empty-icon").textContent = "⚠️";
        emptyState.querySelector("h3").textContent = "Scan Failed";
        emptyState.querySelector("p").textContent = errMessage;
        
        resultsContainer.querySelector(".results-list").style.display = "none";
    }

    function clearResults() {
        listDirs.innerHTML = "";
        listFiles.innerHTML = "";
        resultsCounter.textContent = "0 items found";
        btnSegregate.disabled = true;
        
        // Restore default empty state copy
        const emptyState = resultsContainer.querySelector(".empty-state");
        emptyState.querySelector(".empty-icon").textContent = "📂";
        emptyState.querySelector("h3").textContent = "No scan run yet";
        emptyState.querySelector("p").textContent = 'Enter a folder path and click "Scan Directory" above to review Windows-specific files and folders.';
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
