# Windows-Segregation

An elegant, multi-interface Python utility designed to scan folders recursively, identify strictly Windows-specific files and directories, and automatically segregate them into a dedicated `Windows/` folder.

This utility is extremely useful when clean, cross-platform workspaces (e.g. shared via OneDrive or Git repositories) need to be purged of Windows OS configurations, shortcuts, and application caches while preserving their hierarchy.

## Interfaces Available

We provide three different ways to interact with the segregation engine:

1. **Command Line Interface (CLI):** Fast, scriptable terminal utility.
2. **Standalone Desktop GUI:** Clean, dark-themed native Tkinter application.
3. **Local Web Dashboard:** Premium, responsive web dashboard built with Flask and styled with CSS Glassmorphic effects.

---

## 🚀 Installation & Setup

Ensure you have Python 3 installed. Since the core logic and Desktop GUI utilize Python's built-in libraries (`tkinter`, `shutil`, `pathlib`, etc.), you only need to install `Flask` if you wish to run the Web Dashboard.

```bash
# Clone or move to the project folder
cd Windows-Segregation

# (Optional) Install Flask for the Web Dashboard
pip install -r requirements.txt
```

---

## 💻 Running the Interfaces

### 1. Command Line Interface (CLI)
Run the script passing the target directory as an argument:

```bash
# Basic run on current directory
python cli.py

# Scan specific folder
python cli.py /path/to/target/directory

# Include compiled Windows binaries (.exe, .dll)
python cli.py /path/to/target/directory --binaries

# Run a simulation/trial without moving files (Dry Run)
python cli.py /path/to/target/directory --dry-run
```

### 2. Standalone Desktop GUI
Launch the native desktop window:

```bash
python gui.py
```
*Simply browse to select your directory, click **Scan Directory**, review the listed items, and click **Segregate Items** to clean it up.*

### 3. Local Web Dashboard
Launch the Flask server:

```bash
python web.py
```
Once started:
1. Open your browser and navigate to **[http://localhost:5000](http://localhost:5000)**.
2. Enter the folder path you want to scan.
3. Review files in a gorgeous responsive dashboard before executing segregation.

---

## 🔍 How It Decides What Is Windows-Only

The segregator follows default rules to identify files. You can modify these settings directly in the `segregator/core.py` default config block:

### 1. Strictly Windows-Only Extensions
Files with these suffixes are automatically selected:
* `.lnk` (Shell Shortcuts)
* `.url` (Internet Shortcuts)
* `.reg` (Windows Registry scripts)
* `.msi` (Windows Installer packages)
* `.aip` (Advanced Installer projects)
* `.ifp` (InstallForge projects)
* `.bat` / `.cmd` (Windows Command/Batch scripts)

### 2. System/App Folders in Documents
Standard user directories generated natively by Windows or Windows-only desktop programs:
* `AutoHotkey` (Windows hotkey scripts)
* `IISExpress` / `My Web Sites` (Microsoft Web Server configurations)
* `My Games` / `Saved Games` (Native Windows gaming save paths)
* `PowerToys` / `Rainmeter` (Windows personalization tools)
* `UniGetUI` (Windows Package Manager front-end configuration)
* `WindowsPowerShell` / `PowerShell` (Windows shell profile databases/modules)
* `Outlook Files` (Windows-specific `.pst` databases)
* `OneNote Notebooks` (Local `.one` notebooks)
* Game specific folders (e.g., `CD Projekt Red`, `Overwatch`, `Marvel`)

### 3. (Optional) Executable Binaries
* `.exe` / `.dll` (Can be included using the `-b` / `--binaries` options in the CLI, or by checking the "Include Compiled Windows Binaries" checkbox in the GUI/Web UI).
* *Note: Coding projects (e.g., directories containing `.git`, `node_modules`, Unity projects `Library` or `obj` folders) are automatically bypassed during recursive binary scanning to prevent breaking development environment structures.*

---

## Part of a Larger Collection
This project is part of the **[Thunar-Action-Collection](https://github.com/Vikyek/Thunar-Action-Collection)**—a curated collection of custom Thunar action scripts and utilities designed to enhance the Thunar File Manager on Linux. Visit the collection repository for other useful actions and full setup guides.
