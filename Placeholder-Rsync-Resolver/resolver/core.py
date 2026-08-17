import os
import shutil
import subprocess
import tempfile
from pathlib import Path

class PlaceholderResolver:
    def __init__(self, placeholder_dir, actual_source, destination_dir):
        self.placeholder_dir = Path(placeholder_dir).resolve()
        self.actual_source = actual_source  # e.g., local path or remote "user@host:/path"
        self.destination_dir = Path(destination_dir).resolve()

    def scan(self, force_all=False):
        """
        Scans the placeholder directory recursively.
        Returns a dict categorizing files:
        {
            "placeholders": [list of relative path strings (0-byte files)],
            "local_full": [list of relative path strings (>0-byte files)]
        }
        """
        results = {
            "placeholders": [],
            "local_full": []
        }

        if not self.placeholder_dir.exists():
            return results

        for root, _, files in os.walk(self.placeholder_dir):
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.placeholder_dir)
                
                # Skip the destination directory if it is nested inside the source
                try:
                    if file_path.relative_to(self.destination_dir):
                        continue
                except ValueError:
                    pass

                # Check if it's a 0-byte placeholder
                if not force_all and file_path.stat().st_size == 0:
                    results["placeholders"].append(str(rel_path))
                else:
                    if force_all:
                        results["placeholders"].append(str(rel_path))
                    else:
                        results["local_full"].append(str(rel_path))
                        
        return results

    def run_local_copy(self, file_list, progress_callback=None):
        """
        Copies local full-size files directly to the destination.
        """
        total = len(file_list)
        successful = []
        failed = []

        for idx, rel_path in enumerate(file_list):
            src = self.placeholder_dir / rel_path
            dest = self.destination_dir / rel_path
            
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if progress_callback:
                    progress_callback(f"[Local Copy] ({idx+1}/{total}) Copying {rel_path}...")
                
                shutil.copy2(str(src), str(dest))
                successful.append(rel_path)
            except Exception as e:
                failed.append((rel_path, str(e)))
                if progress_callback:
                    progress_callback(f"[Error] Failed to copy {rel_path}: {str(e)}")
                    
        return successful, failed

    def run_rsync(self, file_list, progress_callback=None):
        """
        Uses rsync to fetch placeholder files from the actual source.
        """
        if not file_list:
            return True, "No files to rsync."

        # Ensure destination directory exists
        self.destination_dir.mkdir(parents=True, exist_ok=True)

        # Write relative paths to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt") as temp_file:
            for f in file_list:
                temp_file.write(f + '\n')
            temp_path = temp_file.name

        try:
            # Ensure the actual source path format is correct (trailing slash is key for --files-from)
            source_path = self.actual_source
            if not source_path.endswith('/') and not ':' in source_path:
                source_path += '/'
            elif ':' in source_path and not source_path.endswith('/'):
                # For remote paths like host:dir, make sure it ends with a slash if not specifying a file
                if not source_path.endswith(':'):
                    source_path += '/'

            # Build rsync command
            # -a: archive mode, -v: verbose, -R: relative paths (crucial to preserve folder structure)
            cmd = [
                "rsync",
                "-av",
                "--progress",
                f"--files-from={temp_path}",
                source_path,
                str(self.destination_dir)
            ]
            
            if progress_callback:
                progress_callback(f"Executing command: {' '.join(cmd)}")

            # Run rsync subprocess
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                bufsize=1
            )
            
            # Read stdout stream in real-time
            for line in process.stdout:
                if progress_callback:
                    progress_callback(line.strip())
                    
            process.wait()
            success = (process.returncode == 0)
            
            return success, f"rsync exited with code {process.returncode}"
        except Exception as e:
            return False, str(e)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def verify_transfers(self, file_list):
        """
        Verifies that files exist in the destination and are non-empty.
        """
        successful = []
        failed = []
        for rel_path in file_list:
            dest = self.destination_dir / rel_path
            if dest.exists() and dest.stat().st_size > 0:
                successful.append(rel_path)
            else:
                failed.append(rel_path)
        return successful, failed

    def cleanup_sources(self, file_list, progress_callback=None):
        """
        Deletes source placeholder files (used in move operations).
        """
        deleted = []
        for rel_path in file_list:
            src = self.placeholder_dir / rel_path
            if src.exists():
                try:
                    src.unlink()
                    deleted.append(rel_path)
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"[Cleanup Error] Failed to delete {rel_path}: {str(e)}")

        # Remove empty directories recursively
        self._remove_empty_dirs(self.placeholder_dir)
        return deleted

    def _remove_empty_dirs(self, path):
        if not path.is_dir():
            return

        # Recurse into subdirectories
        for entry in os.scandir(path):
            if entry.is_dir():
                self._remove_empty_dirs(Path(entry.path))

        # Delete current directory if it is empty and not the root placeholder directory itself
        if path != self.placeholder_dir:
            try:
                if not os.listdir(path):
                    path.rmdir()
            except OSError:
                pass
