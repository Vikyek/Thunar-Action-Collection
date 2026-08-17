# Placeholder-Rsync-Resolver

A premium Python file-synchronization tool designed to resolve local 0-byte placeholder files (e.g. dehydrated OneDrive files or unsynchronized remote clones) by copying/moving the actual full-size files from a source directory (local disk or remote server) using **rsync**.

## How It Works Under the Hood

The tool processes file transfers in an optimized pipeline:
1. **Scanning:** Traverses the placeholder directory recursively and partitions files into two groups:
   - **Placeholders:** 0-byte files that need to be fetched.
   - **Local Full-size:** Files that are already fully downloaded locally (size > 0).
2. **Local Transfers:** Copies the local full-size files directly from the placeholder directory to the destination (fast offline copy).
3. **Rsync Transfer:** Writes the list of placeholder files to a temporary file list and runs a single batch `rsync` command using `--files-from`. This avoids running rsync multiple times and leverages rsync's capability to transfer files over SSH or local pathways.
4. **Verification:** Inspects all transferred files in the destination directory to ensure they exist and have a size greater than 0.
5. **Move Cleanup (Optional):** If the action mode is set to `move`, the tool deletes the verified source placeholder files from the placeholder directory and recursively cleans up empty folders.

---

## 🚀 Installation & Setup

Ensure you have Python 3 and the `rsync` utility installed on your Linux system.

```bash
# Move to the project directory
cd Placeholder-Rsync-Resolver

# (Optional) Install Flask for the Web Dashboard
pip install -r requirements.txt
```

---

## 💻 Running the Interfaces

We provide three different ways to interact with the resolver:

### 1. Command Line Interface (CLI)
Run the script passing the required source, actual content source, and destination parameters:

```bash
# Basic copy operation (local source)
python3 cli.py -s /path/to/placeholders -a /mnt/actual_source -d /path/to/destination --action copy

# Move operation with a remote SSH source
python3 cli.py -s /path/to/placeholders -a user@remotehost:/var/sync_source -d /path/to/destination --action move

# Force rsync for all files (skip direct local copy optimization)
python3 cli.py -s /path/to/placeholders -a /mnt/actual_source -d /path/to/destination --force-all

# Run a simulation only (Dry Run)
python3 cli.py -s /path/to/placeholders -a /mnt/actual_source -d /path/to/destination --dry-run
```

### 2. Standalone Desktop GUI
Launch the native desktop window:

```bash
python3 gui.py
```
*Configure directory paths, select your options, scan, and watch the rsync progress stream in the terminal log box.*

### 3. Local Web Dashboard
Launch the Flask server:

```bash
python3 web.py
```
1. Open your browser and navigate to **[http://localhost:5000](http://localhost:5000)**.
2. Fill in the source directories, select the action, and scan.
3. Review files and click **Resolve Placeholders** to watch the real-time rsync transfer logs streamed to the web dashboard.

---

## Part of a Larger Collection
This project is part of the **[Thunar-Action-Collection](https://github.com/Vikyek/Thunar-Action-Collection)**—a curated collection of custom Thunar action scripts and utilities designed to enhance the Thunar File Manager on Linux. Visit the collection repository for other useful actions and full setup guides.
