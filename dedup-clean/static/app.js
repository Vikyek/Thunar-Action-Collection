document.addEventListener("DOMContentLoaded", () => {
    // Inputs & Buttons
    const dirInput = document.getElementById("dir-input");
    const checkRename = document.getElementById("check-rename");
    const checkWinclean = document.getElementById("check-winclean");
    const checkDryRun = document.getElementById("check-dry-run");
    
    const btnScan = document.getElementById("btn-scan");
    const btnExecute = document.getElementById("btn-execute");
    const btnClearTerminal = document.getElementById("btn-clear-terminal");
    
    // UI Layout Blocks
    const statusBar = document.getElementById("status-bar");
    const badgeCounter = document.getElementById("badge-counter");
    const resultsBody = document.getElementById("results-body");
    const consoleScreen = document.getElementById("console-screen");
    
    // Tabs Navigation
    const tabsNav = resultsBody.querySelector(".tabs-nav");
    const tabsContent = resultsBody.querySelector(".tabs-content");
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");
    
    // Tab Lists
    const listDups = document.getElementById("list-dups");
    const listEmpty = document.getElementById("list-empty");
    const listWin = document.getElementById("list-win");
    const listRenames = document.getElementById("list-renames");
    const listDirs = document.getElementById("list-dirs");
    
    // Modal Elements
    const modalBackdrop = document.getElementById("confirm-modal");
    const btnModalCancel = document.getElementById("btn-modal-cancel");
    const btnModalConfirm = document.getElementById("btn-modal-confirm");
    const modalCloseBtn = document.getElementById("modal-close-btn");
    const modalCountDups = document.getElementById("modal-count-dups");
    const modalCountEmpty = document.getElementById("modal-count-empty");

    // Local data state
    let scanResults = {
        duplicates: [],
        empty_deleted: [],
        win_leftovers: [],
        renames: [],
        empty_dirs: []
    };

    // Tab Switching Logic
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.getAttribute("data-tab");
            
            // Remove active classes
            tabBtns.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));
            
            // Set active
            btn.classList.add("active");
            document.getElementById(tabId).classList.add("active");
        });
    });

    // Clear Terminal button
    btnClearTerminal.addEventListener("click", () => {
        consoleScreen.innerHTML = '<div class="screen-placeholder">Waiting for process run...</div>';
    });

    // Scan / Analyze Folder
    btnScan.addEventListener("click", async () => {
        const path = dirInput.value.trim();
        if (!path) {
            updateStatus("Error: Target directory path is required.", true);
            return;
        }

        btnScan.disabled = true;
        btnScan.textContent = "Analyzing...";
        updateStatus("Analyzing folder contents...");
        
        try {
            const response = await fetch("/api/scan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    directory: path,
                    no_rename: !checkRename.checked,
                    no_win_clean: !checkWinclean.checked
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                scanResults = data;
                renderScanResults(data);
            } else {
                showErrorState(data.error || "An error occurred during analysis.");
            }
        } catch (err) {
            showErrorState("Network error: Failed to connect to server.");
        } finally {
            btnScan.disabled = false;
            btnScan.textContent = "Analyze Folder";
        }
    });

    // Run Cleanup Button triggers Modal
    btnExecute.addEventListener("click", () => {
        const totalItems = scanResults.duplicates.length + scanResults.empty_deleted.length;
        
        // Setup Modal Counts
        modalCountDups.textContent = scanResults.duplicates.length;
        modalCountEmpty.textContent = scanResults.empty_deleted.length;
        
        // Open Modal
        modalBackdrop.style.display = "flex";
    });

    // Close Modal triggers
    const closeModal = () => {
        modalBackdrop.style.display = "none";
    };
    btnModalCancel.addEventListener("click", closeModal);
    modalCloseBtn.addEventListener("click", closeModal);
    modalBackdrop.addEventListener("click", (e) => {
        if (e.target === modalBackdrop) closeModal();
    });

    // Confirm Cleanup Modal click starts SSE Stream
    btnModalConfirm.addEventListener("click", () => {
        closeModal();
        
        const path = dirInput.value.trim();
        
        // Disable controls
        btnScan.disabled = true;
        btnExecute.disabled = true;
        
        // Clear terminal logs
        consoleScreen.innerHTML = "";
        
        // Build query params
        const params = new URLSearchParams({
            directory: path,
            no_rename: !checkRename.checked,
            no_win_clean: !checkWinclean.checked,
            dry_run: checkDryRun.checked
        });
        
        updateStatus("Initializing cleanup job...");
        
        // Start EventSource stream
        const eventSource = new EventSource(`/api/execute/stream?${params.toString()}`);
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.event === "start") {
                updateStatus(data.message);
                appendTerminalLine(data.message, "cmd");
            } else if (data.event === "progress") {
                updateStatus(`Progress: ${data.progress}% - ${data.message}`);
                appendTerminalLine(`[${data.progress}%] ${data.message}`);
            } else if (data.event === "done") {
                updateStatus(data.message);
                appendTerminalLine(data.message, "success");
                
                // Print execution summary
                const sum = data.summary;
                appendTerminalLine("\n=== Execution Summary ===", "cmd");
                appendTerminalLine(`• Files Scanned: ${sum.scanned_files}`);
                appendTerminalLine(`• Empty Files Deleted: ${sum.empty_deleted}`);
                appendTerminalLine(`• Windows leftovers cleaned: ${sum.win_leftovers}`);
                appendTerminalLine(`• Duplicate Files Deleted: ${sum.duplicates_deleted}`);
                appendTerminalLine(`• Copy Suffixes Renamed: ${sum.renamed_files}`);
                appendTerminalLine(`• Empty Folders Deleted: ${sum.empty_dirs}`);
                appendTerminalLine(`• Disk Space Reclaimed: ${sum.saved_mb.toFixed(2)} MB`);
                appendTerminalLine("=== Process Complete ===\n", "success");
                
                eventSource.close();
                
                // Re-enable actions & trigger re-analyze to clear list
                btnScan.disabled = false;
                btnScan.click();
            } else if (data.event === "error") {
                updateStatus("Error: " + data.message, true);
                appendTerminalLine(`[Error] ${data.message}`, "error");
                eventSource.close();
                
                btnScan.disabled = false;
                btnExecute.disabled = false;
            }
        };
        
        eventSource.onerror = () => {
            updateStatus("Error: Connection to deduplication stream lost.", true);
            appendTerminalLine("[Error] Server-Sent Events stream disconnected.", "error");
            eventSource.close();
            
            btnScan.disabled = false;
            btnExecute.disabled = false;
        };
    });

    function renderScanResults(data) {
        const dupsCount = data.duplicates.length;
        const emptyCount = data.empty_deleted.length;
        const winCount = data.win_leftovers.length;
        const renamesCount = data.renames.length;
        const dirsCount = data.empty_dirs.length;
        
        const totalItems = dupsCount + emptyCount + winCount + renamesCount + dirsCount;
        badgeCounter.textContent = `${totalItems} item${totalItems === 1 ? "" : "s"} found`;
        
        listDups.innerHTML = "";
        listEmpty.innerHTML = "";
        listWin.innerHTML = "";
        listRenames.innerHTML = "";
        listDirs.innerHTML = "";
        
        if (totalItems === 0) {
            showEmptyState();
            btnExecute.disabled = true;
            updateStatus("Scan finished. Clean directory!");
            return;
        }
        
        // Display tabs
        resultsBody.classList.remove("empty");
        resultsBody.querySelector(".empty-state").style.display = "none";
        tabsNav.style.display = "flex";
        tabsContent.style.display = "block";
        
        // 1. Populate Duplicates
        if (dupsCount > 0) {
            data.duplicates.forEach(file => {
                const li = document.createElement("li");
                li.textContent = file;
                listDups.appendChild(li);
            });
        } else {
            listDups.innerHTML = '<li class="empty-list-note">No duplicate files found.</li>';
        }
        
        // 2. Populate Empty Files
        if (emptyCount > 0) {
            data.empty_deleted.forEach(file => {
                const li = document.createElement("li");
                li.textContent = file;
                listEmpty.appendChild(li);
            });
        } else {
            listEmpty.innerHTML = '<li class="empty-list-note">No empty files found.</li>';
        }
        
        // 3. Populate Windows Leftovers
        if (winCount > 0) {
            data.win_leftovers.forEach(file => {
                const li = document.createElement("li");
                li.textContent = file;
                listWin.appendChild(li);
            });
        } else {
            listWin.innerHTML = '<li class="empty-list-note">No Windows leftovers found.</li>';
        }
        
        // 4. Populate Renames
        if (renamesCount > 0) {
            data.renames.forEach(pair => {
                const li = document.createElement("li");
                li.textContent = `${pair[0]} ➔ ${pair[1].split('/').pop()}`;
                listRenames.appendChild(li);
            });
        } else {
            listRenames.innerHTML = '<li class="empty-list-note">No files to rename.</li>';
        }
        
        // 5. Populate Empty Folders
        if (dirsCount > 0) {
            data.empty_dirs.forEach(dir => {
                const li = document.createElement("li");
                li.textContent = dir;
                listDirs.appendChild(li);
            });
        } else {
            listDirs.innerHTML = '<li class="empty-list-note">No empty folders found.</li>';
        }
        
        btnExecute.disabled = false;
        updateStatus(`Scan complete. Found ${dupsCount} duplicates and ${emptyCount} empty files. Ready to cleanup.`);
    }

    function showEmptyState() {
        resultsBody.classList.add("empty");
        resultsBody.querySelector(".empty-state").style.display = "flex";
        tabsNav.style.display = "none";
        tabsContent.style.display = "none";
        
        const emptyState = resultsBody.querySelector(".empty-state");
        emptyState.querySelector(".empty-icon").textContent = "🔍";
        emptyState.querySelector("h3").textContent = "No folder analyzed yet";
        emptyState.querySelector("p").textContent = 'Configure the target directory path and click "Analyze Folder" on the left to see scan results.';
    }

    function showErrorState(errMessage) {
        scanResults = { duplicates: [], empty_deleted: [], win_leftovers: [], renames: [], empty_dirs: [] };
        listDups.innerHTML = "";
        listEmpty.innerHTML = "";
        listWin.innerHTML = "";
        listRenames.innerHTML = "";
        listDirs.innerHTML = "";
        badgeCounter.textContent = "0 items found";
        btnExecute.disabled = true;
        
        resultsBody.classList.add("empty");
        const emptyState = resultsBody.querySelector(".empty-state");
        emptyState.style.display = "flex";
        emptyState.querySelector(".empty-icon").textContent = "⚠️";
        emptyState.querySelector("h3").textContent = "Analysis Failed";
        emptyState.querySelector("p").textContent = errMessage;
        
        tabsNav.style.display = "none";
        tabsContent.style.display = "none";
        
        updateStatus("Error: " + errMessage, true);
    }

    function appendTerminalLine(message, type = "") {
        const div = document.createElement("div");
        div.className = "log-line " + type;
        div.textContent = message;
        consoleScreen.appendChild(div);
        consoleScreen.scrollTop = consoleScreen.scrollHeight;
    }

    function updateStatus(message, isError = false) {
        statusBar.textContent = message;
        if (isError) {
            statusBar.style.color = "var(--color-primary)";
        } else {
            statusBar.style.color = "var(--text-muted)";
        }
    }
});
