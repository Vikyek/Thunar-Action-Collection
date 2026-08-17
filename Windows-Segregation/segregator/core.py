import os
import shutil
import json
from pathlib import Path

# Default configuration rules
DEFAULT_CONFIG = {
    "windows_extensions": [
        ".lnk", ".url", ".reg", ".bat", ".cmd", ".msi", ".aip", ".ifp"
    ],
    "windows_binary_extensions": [
        ".exe", ".dll"
    ],
    "windows_dir_names": [
        "autohotkey", "iisexpress", "my games", "my web sites", 
        "onenote notebooks", "outlook files", "saved games", 
        "unigetui", "windowspowershell", "powertoys", "rainmeter", 
        "drivereasy", "custom installers", "custom instalers",
        "marvel rivals vortex extension", "microdicomdb", "overwatch", 
        "cd projekt red", "marvel", "guild wars 2"
    ],
    "exclude_dirs": [
        ".git", "node_modules", "library", "obj", "temp", "bin/debug", "bin/release", "windows"
    ]
}

class SegregatorEngine:
    def __init__(self, target_dir, config=None):
        self.target_dir = Path(target_dir).resolve()
        self.config = config or DEFAULT_CONFIG
        self.windows_dir = self.target_dir / "Windows"
        
        # Normalize comparison lists
        self.win_exts = {ext.lower() for ext in self.config["windows_extensions"]}
        self.bin_exts = {ext.lower() for ext in self.config["windows_binary_extensions"]}
        self.win_dirs = {name.lower() for name in self.config["windows_dir_names"]}
        self.exclude_dirs = {name.lower() for name in self.config["exclude_dirs"]}

    def scan(self, include_binaries=False):
        """
        Scans the target directory recursively.
        Returns a dictionary of found items:
        {
            "directories": [list of Path objects to move],
            "files": [list of Path objects to move]
        }
        """
        items_to_move = {
            "directories": [],
            "files": []
        }
        
        if not self.target_dir.exists():
            return items_to_move

        self._scan_directory(self.target_dir, items_to_move, include_binaries)
        return items_to_move

    def _should_exclude(self, path: Path):
        # Don't scan the target Windows folder itself
        if path == self.windows_dir:
            return True
        
        # Check against exclusions list (both exact match and segments of path)
        parts = [p.lower() for p in path.relative_to(self.target_dir).parts]
        for part in parts:
            if part in self.exclude_dirs:
                return True
        return False

    def _scan_directory(self, current_dir: Path, items_to_move, include_binaries):
        try:
            for entry in os.scandir(current_dir):
                entry_path = Path(entry.path)
                
                # Check exclusions
                if self._should_exclude(entry_path):
                    continue
                
                if entry.is_dir():
                    # Check if the directory itself is Windows-only
                    if entry.name.lower() in self.win_dirs:
                        items_to_move["directories"].append(entry_path)
                    else:
                        # Recursively scan directory
                        self._scan_directory(entry_path, items_to_move, include_binaries)
                elif entry.is_file():
                    ext = entry_path.suffix.lower()
                    
                    # Check if file has a Windows-only extension
                    if ext in self.win_exts:
                        items_to_move["files"].append(entry_path)
                    # Optionally check for compiled binaries
                    elif include_binaries and ext in self.bin_exts:
                        items_to_move["files"].append(entry_path)
        except PermissionError:
            # Skip folders we don't have access to
            pass

    def segregate(self, items, dry_run=False):
        """
        Moves the items to the Windows folder.
        """
        results = {
            "moved_directories": [],
            "moved_files": [],
            "errors": []
        }
        
        if dry_run:
            results["moved_directories"] = [str(p.relative_to(self.target_dir)) for p in items["directories"]]
            results["moved_files"] = [str(p.relative_to(self.target_dir)) for p in items["files"]]
            return results

        # Create Windows directory if not exists
        if (items["directories"] or items["files"]) and not self.windows_dir.exists():
            self.windows_dir.mkdir(parents=True, exist_ok=True)

        # Move directories
        for dir_path in items["directories"]:
            if not dir_path.exists():
                continue
            try:
                # Calculate relative path to preserve hierarchy if needed, 
                # but for top-level dirs we just move them directly to Windows/DirName
                rel_path = dir_path.relative_to(self.target_dir)
                dest_path = self.windows_dir / rel_path
                
                # Ensure destination parent exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Handle existing folder at destination
                if dest_path.exists():
                    shutil.rmtree(dest_path)
                
                shutil.move(str(dir_path), str(dest_path))
                results["moved_directories"].append((str(rel_path), str(dest_path.relative_to(self.target_dir))))
            except Exception as e:
                results["errors"].append(f"Error moving directory {dir_path.name}: {str(e)}")

        # Move files
        for file_path in items["files"]:
            if not file_path.exists():
                continue
            try:
                rel_path = file_path.relative_to(self.target_dir)
                dest_path = self.windows_dir / rel_path
                
                # Ensure destination parent exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Handle existing file at destination
                if dest_path.exists():
                    dest_path.unlink()
                
                shutil.move(str(file_path), str(dest_path))
                results["moved_files"].append((str(rel_path), str(dest_path.relative_to(self.target_dir))))
            except Exception as e:
                results["errors"].append(f"Error moving file {file_path.name}: {str(e)}")

        return results
