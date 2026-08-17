#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
from flask import Flask, jsonify, request, render_template, Response

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from dedup import DeduplicatorEngine

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route("/")
def index():
    default_dir = os.getcwd()
    return render_template("index.html", default_dir=default_dir)

@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json() or {}
    directory = data.get("directory", "")
    no_rename = data.get("no_rename", False)
    no_win_clean = data.get("no_win_clean", False)
    
    if not directory:
        return jsonify({"success": False, "error": "Directory path is required."}), 400
        
    path = Path(directory).resolve()
    if not path.exists() or not path.is_dir():
        return jsonify({"success": False, "error": "Directory does not exist."}), 400
        
    try:
        engine = DeduplicatorEngine([path])
        # Run a dry-run scan to gather candidates
        results = engine.run_deduplication(
            no_rename=no_rename,
            no_win_clean=no_win_clean,
            dry_run=True
        )
        
        return jsonify({
            "success": True,
            "scanned_files": results["scanned_files"],
            "empty_deleted": results["empty_deleted"],
            "win_leftovers": results["win_leftovers_deleted"],
            "duplicates": results["duplicates_deleted"],
            "renames": results["renamed_files"],
            "empty_dirs": results["empty_dirs_deleted"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/execute/stream")
def api_execute_stream():
    directory = request.args.get("directory", "")
    no_rename = request.args.get("no_rename") == "true"
    no_win_clean = request.args.get("no_win_clean") == "true"
    dry_run = request.args.get("dry_run") == "true"
    
    if not directory:
        def err_gen():
            yield "data: " + json.dumps({"event": "error", "message": "Directory parameter is required."}) + "\n\n"
        return Response(err_gen(), mimetype="text/event-stream")

    path = Path(directory).resolve()
    
    def generate():
        yield "data: " + json.dumps({"event": "start", "message": f"Initializing cleanup on {path.name}..."}) + "\n\n"
        
        try:
            engine = DeduplicatorEngine([path])
            
            def sse_progress(pct, msg):
                # Send progress update event
                import json
                sys.stdout.write(f"Progress: {pct}% - {msg}\n")
                sys.stdout.flush()
                # Yield SSE chunk
                # We use a global/nonlocal reference or inline yield
            
            # Since yielding from nested functions in Python is complex, 
            # we can run it step-by-step or pass a callback that enqueues messages, 
            # or simply run the engine with a custom progress monitor.
            # To yield in real-time, we will override the progress callback to write to SSE format
            
        except Exception as e:
            yield "data: " + json.dumps({"event": "error", "message": str(e)}) + "\n\n"
            return

        # Let's write a generator-safe wrapper for engine deduplication
        try:
            # Step 1: Scan
            yield "data: " + json.dumps({"event": "progress", "progress": 10, "message": "Scanning files in directory tree..."}) + "\n\n"
            all_files = []
            win_leftovers_deleted = []
            for root, dirs, files in os.walk(str(path), topdown=True):
                if not no_win_clean:
                    for d in list(dirs):
                        if d.lower() in ("system volume information", "$recycle.bin"):
                            dirpath = Path(root) / d
                            try:
                                if not dry_run:
                                    shutil.rmtree(str(dirpath))
                                win_leftovers_deleted.append(str(dirpath))
                            except Exception:
                                pass
                            dirs.remove(d)
                for file in files:
                    filepath = Path(root) / file
                    if not filepath.is_symlink():
                        if not no_win_clean and engine.is_windows_leftover(filepath):
                            try:
                                if not dry_run:
                                    filepath.unlink()
                                win_leftovers_deleted.append(str(filepath))
                            except Exception:
                                pass
                        else:
                            all_files.append(filepath)

            total_files = len(all_files)
            yield "data: " + json.dumps({"event": "progress", "progress": 20, "message": f"Scan complete. Found {total_files} files."}) + "\n\n"
            
            # Step 2: Empty Files
            empty_deleted = []
            size_groups = {}
            for idx, filepath in enumerate(all_files):
                try:
                    if filepath.exists():
                        size = filepath.stat().st_size
                        if size == 0:
                            if not dry_run:
                                filepath.unlink()
                            empty_deleted.append(str(filepath))
                        else:
                            if size not in size_groups:
                                size_groups[size] = []
                            size_groups[size].append(filepath)
                except Exception:
                    pass
                if idx % 100 == 0 and total_files > 0:
                    pct = 20 + int((idx / total_files) * 15)
                    yield "data: " + json.dumps({"event": "progress", "progress": pct, "message": f"Filtering empty files ({idx}/{total_files})..."}) + "\n\n"

            # Step 3: Hash Candidates
            hash_candidates = []
            for size, paths in size_groups.items():
                if len(paths) >= 2:
                    hash_candidates.extend(paths)

            total_candidates = len(hash_candidates)
            hash_groups = {}
            
            # Step 4: Hash
            if total_candidates > 0:
                for idx, filepath in enumerate(hash_candidates):
                    file_hash = engine.get_file_hash(filepath)
                    if file_hash:
                        if file_hash not in hash_groups:
                            hash_groups[file_hash] = []
                        hash_groups[file_hash].append(filepath)
                    else:
                        try:
                            if filepath.exists():
                                size = filepath.stat().st_size
                                clean_base, ext = engine.get_clean_base_name(filepath)
                                fallback_key = f"unreadable:{size}:{clean_base}:{ext}"
                                if fallback_key not in hash_groups:
                                    hash_groups[fallback_key] = []
                                hash_groups[fallback_key].append(filepath)
                        except Exception:
                            pass
                    if idx % 50 == 0:
                        pct = 35 + int((idx / total_candidates) * 45)
                        yield "data: " + json.dumps({"event": "progress", "progress": pct, "message": f"Hashing duplicate candidates ({idx}/{total_candidates})..."}) + "\n\n"
            
            engine.save_cache()

            # Step 5: Delete duplicates
            duplicates = {h: paths for h, paths in hash_groups.items() if len(paths) > 1}
            total_duplicates = sum(len(paths) - 1 for paths in duplicates.values())
            duplicates_deleted = []
            saved_space_bytes = 0
            
            if total_duplicates > 0:
                deleted_count = 0
                for file_hash, paths in duplicates.items():
                    file_infos = []
                    for p in paths:
                        try:
                            if p.exists():
                                stat = p.stat()
                                file_infos.append((stat.st_mtime, p, stat.st_size))
                        except Exception:
                            pass
                    if not file_infos:
                        continue
                    file_infos.sort(key=lambda x: (x[0], len(str(x[1])), x[1]))
                    
                    for mtime, p, size in file_infos[1:]:
                        try:
                            if not dry_run:
                                p.unlink()
                            duplicates_deleted.append(str(p))
                            saved_space_bytes += size
                            deleted_count += 1
                        except Exception:
                            pass
                        if deleted_count % 5 == 0:
                            pct = 80 + int((deleted_count / total_duplicates) * 10)
                            yield "data: " + json.dumps({"event": "progress", "progress": pct, "message": f"Deleting duplicate files ({deleted_count}/{total_duplicates})..."}) + "\n\n"

            engine.save_cache()

            # Step 6: Renames
            renamed_files = []
            if not no_rename:
                yield "data: " + json.dumps({"event": "progress", "progress": 90, "message": "Cleaning file copy suffixes..."}) + "\n\n"
                for root, _, files in os.walk(str(path)):
                    for file in files:
                        filepath = Path(root) / file
                        if not filepath.is_symlink():
                            new_filepath, renamed = engine.remove_copy_suffix(filepath)
                            if renamed:
                                renamed_files.append((str(filepath), str(new_filepath)))

            engine.save_cache()

            # Step 7: Clean folders
            empty_dirs_deleted = []
            yield "data: " + json.dumps({"event": "progress", "progress": 95, "message": "Cleaning up empty directories..."}) + "\n\n"
            for root, dirs, files in os.walk(str(path), topdown=False):
                if Path(root) == path:
                    continue
                try:
                    if not os.listdir(root):
                        if not dry_run:
                            os.rmdir(root)
                        empty_dirs_deleted.append(root)
                except Exception:
                    pass

            yield "data: " + json.dumps({"event": "progress", "progress": 100, "message": "Cleanup complete."}) + "\n\n"
            
            # Send done event with summary results
            yield "data: " + json.dumps({
                "event": "done",
                "message": "Cleanup executed successfully!" if not dry_run else "Simulation scan completed successfully!",
                "summary": {
                    "scanned_files": total_files,
                    "empty_deleted": len(empty_deleted),
                    "win_leftovers": len(win_leftovers_deleted),
                    "duplicates_deleted": len(duplicates_deleted),
                    "renamed_files": len(renamed_files),
                    "empty_dirs": len(empty_dirs_deleted),
                    "saved_mb": saved_space_bytes / 1024 / 1024
                }
            }) + "\n\n"
            
        except Exception as e:
            yield "data: " + json.dumps({"event": "error", "message": str(e)}) + "\n\n"

    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    print("Starting Dedup Web Server...")
    print("Open http://localhost:5000 in your browser.")
    app.run(host="127.0.0.1", port=5000, debug=True)
