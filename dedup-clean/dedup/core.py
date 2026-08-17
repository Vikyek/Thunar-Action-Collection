import os
import sys
import hashlib
import time
import json
import shutil
import re
from pathlib import Path
from collections import defaultdict

class DeduplicatorEngine:
    def __init__(self, directories, cache_dir=None):
        self.directories = [Path(d).resolve() for d in directories]
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "dedup-clean"
        self.cache_file = self.cache_dir / "hash_cache.json"
        self.cache = self.load_cache()
        self.cache_dirty = False

    def load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_cache(self):
        if not self.cache_dirty:
            return
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f)
            self.cache_dirty = False
        except Exception:
            pass

    def get_file_hash(self, filepath):
        try:
            stat = filepath.stat()
            mtime = stat.st_mtime
            size = stat.st_size
        except Exception:
            return None
            
        fp_str = str(filepath)
        if fp_str in self.cache:
            cached_mtime, cached_size, cached_hash = self.cache[fp_str]
            if cached_mtime == mtime and cached_size == size:
                if cached_hash == "unreadable":
                    return None
                return cached_hash
                
        hasher = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            file_hash = hasher.hexdigest()
            self.cache[fp_str] = [mtime, size, file_hash]
            self.cache_dirty = True
            return file_hash
        except Exception:
            self.cache[fp_str] = [mtime, size, "unreadable"]
            self.cache_dirty = True
            return None

    def get_clean_base_name(self, filepath):
        filename = filepath.name
        base, ext = os.path.splitext(filename)
        
        copy_pattern = re.compile(r'(\s*-\s*Copy|\s*\(\d+\)|\s*-\s*Copy\s*\(\d+\)|\s*Copy\s*of\s*)+$', re.IGNORECASE)
        prefix_pattern = re.compile(r'^Copy\s+of\s+', re.IGNORECASE)
        conflict_pattern = re.compile(r'-(?:V-PC|DESKTOP-[A-Z0-9]+|Latitude[A-Z0-9_-]*)(?:-[A-Z0-9_-]+)?$', re.IGNORECASE)
        
        last_base = None
        while base != last_base:
            last_base = base
            base = copy_pattern.sub('', base).strip()
            base = conflict_pattern.sub('', base).strip()
            base = prefix_pattern.sub('', base).strip()
            
        return base.lower(), ext.lower()

    def remove_copy_suffix(self, filepath):
        dirname = filepath.parent
        base, ext = os.path.splitext(filepath.name)
        
        new_base = re.sub(r'(\s*-\s*[Cc]opy)+$', '', base)
        
        if new_base != base:
            new_filename = new_base + ext
            new_filepath = dirname / new_filename
            
            if not new_filepath.exists():
                try:
                    os.rename(str(filepath), str(new_filepath))
                    fp_str = str(filepath)
                    nfp_str = str(new_filepath)
                    if fp_str in self.cache:
                        self.cache[nfp_str] = self.cache[fp_str]
                        del self.cache[fp_str]
                        self.cache_dirty = True
                    return new_filepath, True
                except Exception:
                    pass
        return filepath, False

    def is_windows_leftover(self, filepath):
        lower_name = filepath.name.lower()
        if lower_name in ("desktop.ini", "thumbs.db"):
            return True
        if lower_name.endswith(".lnk"):
            return True
        return False

    def run_deduplication(self, no_rename=False, no_win_clean=False, progress_callback=None, dry_run=False):
        """
        Executes scanning, hash comparison, deduplication, copy suffix removal, 
        leftovers deletion, and empty directories cleaning.
        """
        results = {
            "scanned_files": 0,
            "empty_deleted": [],
            "win_leftovers_deleted": [],
            "duplicates_deleted": [],
            "renamed_files": [],
            "empty_dirs_deleted": [],
            "saved_space_bytes": 0
        }

        # Step 1: Scan files
        if progress_callback:
            progress_callback(10, "Scanning files in directory tree...")
            
        all_files = []
        for root_dir in self.directories:
            if not root_dir.exists() or not root_dir.is_dir():
                continue
            for root, dirs, files in os.walk(str(root_dir), topdown=True):
                # Clean windows system directory entries
                if not no_win_clean:
                    for d in list(dirs):
                        if d.lower() in ("system volume information", "$recycle.bin"):
                            dirpath = Path(root) / d
                            try:
                                if not dry_run:
                                    shutil.rmtree(str(dirpath))
                                results["win_leftovers_deleted"].append(str(dirpath))
                            except Exception:
                                pass
                            dirs.remove(d)
                            
                for file in files:
                    filepath = Path(root) / file
                    if not filepath.is_symlink():
                        if not no_win_clean and self.is_windows_leftover(filepath):
                            try:
                                if not dry_run:
                                    filepath.unlink()
                                    fp_str = str(filepath)
                                    if fp_str in self.cache:
                                        del self.cache[fp_str]
                                        self.cache_dirty = True
                                results["win_leftovers_deleted"].append(str(filepath))
                            except Exception:
                                pass
                        else:
                            all_files.append(filepath)

        total_files = len(all_files)
        results["scanned_files"] = total_files
        
        if total_files == 0:
            if progress_callback:
                progress_callback(100, "Scanning complete. No files found.")
            return results

        # Step 2: Delete empty files & group by size
        if progress_callback:
            progress_callback(20, "Analyzing file sizes...")
            
        size_groups = defaultdict(list)
        for idx, filepath in enumerate(all_files):
            try:
                if filepath.exists():
                    size = filepath.stat().st_size
                    if size == 0:
                        if not dry_run:
                            filepath.unlink()
                            fp_str = str(filepath)
                            if fp_str in self.cache:
                                del self.cache[fp_str]
                                self.cache_dirty = True
                        results["empty_deleted"].append(str(filepath))
                    else:
                        size_groups[size].append(filepath)
            except Exception:
                pass
                
            if progress_callback and idx % 200 == 0:
                progress = 20 + int((idx / total_files) * 15)
                progress_callback(progress, f"Filtering empty files ({idx}/{total_files})...")

        # Step 3: Identify candidates for hashing (sizes with >= 2 files)
        hash_candidates = []
        for size, paths in size_groups.items():
            if len(paths) >= 2:
                hash_candidates.extend(paths)

        total_candidates = len(hash_candidates)
        
        # Step 4: Hash files
        hash_groups = defaultdict(list)
        if total_candidates > 0:
            for idx, filepath in enumerate(hash_candidates):
                file_hash = self.get_file_hash(filepath)
                if file_hash:
                    hash_groups[file_hash].append(filepath)
                else:
                    # Fallback for unreadable files
                    try:
                        if filepath.exists():
                            size = filepath.stat().st_size
                            clean_base, ext = self.get_clean_base_name(filepath)
                            fallback_key = f"unreadable:{size}:{clean_base}:{ext}"
                            hash_groups[fallback_key].append(filepath)
                    except Exception:
                        pass
                        
                if progress_callback and idx % 100 == 0:
                    progress = 35 + int((idx / total_candidates) * 45)
                    progress_callback(progress, f"Hashing files ({idx}/{total_candidates})...")

        # Save cache
        self.save_cache()

        # Step 5: Process duplicates
        duplicates = {h: paths for h, paths in hash_groups.items() if len(paths) > 1}
        total_duplicates = sum(len(paths) - 1 for paths in duplicates.values())
        
        if total_duplicates > 0:
            deleted_count = 0
            for file_hash, paths in duplicates.items():
                file_infos = []
                for path in paths:
                    try:
                        if path.exists():
                            stat = path.stat()
                            file_infos.append((stat.st_mtime, path, stat.st_size))
                    except Exception:
                        pass
                
                if not file_infos:
                    continue
                    
                # Sort by mtime (oldest first), path length (shortest first), name
                file_infos.sort(key=lambda x: (x[0], len(str(x[1])), x[1]))
                
                # Keep first file, delete the rest
                for mtime, path, size in file_infos[1:]:
                    try:
                        if not dry_run:
                            path.unlink()
                            fp_str = str(path)
                            if fp_str in self.cache:
                                del self.cache[fp_str]
                                self.cache_dirty = True
                        results["duplicates_deleted"].append(str(path))
                        results["saved_space_bytes"] += size
                        deleted_count += 1
                    except Exception:
                        pass
                        
                    if progress_callback and deleted_count % 10 == 0:
                        progress = 80 + int((deleted_count / total_duplicates) * 10)
                        progress_callback(progress, f"Deleting duplicate files ({deleted_count}/{total_duplicates})...")

        # Save cache again
        self.save_cache()

        # Step 6: Rename files containing ' - Copy' suffixes
        if not no_rename:
            if progress_callback:
                progress_callback(90, "Cleaning file copy suffixes...")
            for root_dir in self.directories:
                if not root_dir.exists():
                    continue
                for root, _, files in os.walk(str(root_dir)):
                    for file in files:
                        filepath = Path(root) / file
                        if not filepath.is_symlink():
                            new_filepath, renamed = self.remove_copy_suffix(filepath)
                            if renamed:
                                results["renamed_files"].append((str(filepath), str(new_filepath)))

        self.save_cache()

        # Step 7: Delete empty directories bottom-up
        if progress_callback:
            progress_callback(95, "Cleaning up empty directories...")
        for root_dir in self.directories:
            if not root_dir.exists():
                continue
            for root, dirs, files in os.walk(str(root_dir), topdown=False):
                # Don't delete the root target folder itself
                if Path(root) == root_dir:
                    continue
                try:
                    if not os.listdir(root):
                        if not dry_run:
                            os.rmdir(root)
                        results["empty_dirs_deleted"].append(root)
                except Exception:
                    pass

        if progress_callback:
            progress_callback(100, "Deduplication and cleanup completed.")

        return results
