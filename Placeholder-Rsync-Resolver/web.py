#!/usr/bin/env python3
import os
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from flask import Flask, jsonify, request, render_template, Response

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from resolver import PlaceholderResolver

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route("/")
def index():
    default_dir = os.getcwd()
    return render_template("index.html", default_dir=default_dir)

@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json() or {}
    src_dir = data.get("src_dir", "")
    actual_source = data.get("actual_source", "")
    dest_dir = data.get("dest_dir", "")
    force_all = data.get("force_all", False)
    
    if not src_dir:
        return jsonify({"success": False, "error": "Placeholder directory path is required."}), 400
        
    src_path = Path(src_dir).resolve()
    if not src_path.exists() or not src_path.is_dir():
        return jsonify({"success": False, "error": "Placeholder directory does not exist."}), 400
        
    try:
        # Pass dummy destination to initiate scan
        resolver = PlaceholderResolver(src_path, actual_source, dest_dir or os.getcwd())
        scan_data = resolver.scan(force_all=force_all)
        
        return jsonify({
            "success": True,
            "placeholders": scan_data["placeholders"],
            "local_full": scan_data["local_full"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/resolve/stream")
def stream_resolve():
    src = request.args.get("src", "")
    actual = request.args.get("actual", "")
    dest = request.args.get("dest", "")
    action = request.args.get("action", "copy")
    force_all = request.args.get("force_all") == "true"
    
    if not src or not actual or not dest:
        def err_gen():
            yield "data: " + json.dumps({"event": "error", "message": "Missing required parameters (src, actual, dest)"}) + "\n\n"
        return Response(err_gen(), mimetype="text/event-stream")

    src_path = Path(src).resolve()
    dest_path = Path(dest).resolve()

    def generate():
        resolver = PlaceholderResolver(src_path, actual, dest_path)
        
        # Scan to get files
        scan_data = resolver.scan(force_all=force_all)
        placeholders = scan_data["placeholders"]
        local_full = scan_data["local_full"]
        
        yield "data: " + json.dumps({"event": "start", "message": f"Starting {action} resolution..."}) + "\n\n"
        
        # 1. Local copy
        copied = []
        if local_full:
            yield "data: " + json.dumps({"event": "log", "message": "=== Starting Local Copy ==="}) + "\n\n"
            for idx, rel_path in enumerate(local_full):
                msg = f"[Local Copy] ({idx+1}/{len(local_full)}) Copying {rel_path}..."
                yield "data: " + json.dumps({"event": "log", "message": msg}) + "\n\n"
                
                try:
                    s_path = resolver.placeholder_dir / rel_path
                    d_path = resolver.destination_dir / rel_path
                    d_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(s_path), str(d_path))
                    copied.append(rel_path)
                except Exception as e:
                    yield "data: " + json.dumps({"event": "log", "message": f"[Error] Failed to copy {rel_path}: {str(e)}"}) + "\n\n"

        # 2. Rsync fetch
        if placeholders:
            yield "data: " + json.dumps({"event": "log", "message": "=== Starting Rsync Fetch ==="}) + "\n\n"
            
            # Write files list to temp file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt") as temp_file:
                for f in placeholders:
                    temp_file.write(f + '\n')
                temp_path = temp_file.name
                
            try:
                # Ensure the actual source format is correct
                source_path = resolver.actual_source
                if not source_path.endswith('/') and not ':' in source_path:
                    source_path += '/'
                elif ':' in source_path and not source_path.endswith('/'):
                    if not source_path.endswith(':'):
                        source_path += '/'
                
                cmd = [
                    "rsync",
                    "-av",
                    "--progress",
                    f"--files-from={temp_path}",
                    source_path,
                    str(resolver.destination_dir)
                ]
                
                yield "data: " + json.dumps({"event": "log", "message": f"Executing: {' '.join(cmd)}"}) + "\n\n"
                
                process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True, 
                    bufsize=1
                )
                
                # Stream rsync stdout
                for line in process.stdout:
                    yield "data: " + json.dumps({"event": "log", "message": line.strip()}) + "\n\n"
                    
                process.wait()
                if process.returncode == 0:
                    yield "data: " + json.dumps({"event": "log", "message": "[Rsync] Fetch complete successfully."}) + "\n\n"
                else:
                    yield "data: " + json.dumps({"event": "log", "message": f"[Rsync Error] Exited with code {process.returncode}"}) + "\n\n"
            except Exception as e:
                yield "data: " + json.dumps({"event": "log", "message": f"[Rsync Exception] {str(e)}"}) + "\n\n"
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        # 3. Verification
        yield "data: " + json.dumps({"event": "log", "message": "=== Starting Verification ==="}) + "\n\n"
        verified, failed = resolver.verify_transfers(placeholders + local_full)
        
        yield "data: " + json.dumps({"event": "log", "message": f"Verification results: {len(verified)} successfully verified, {len(failed)} failed."}) + "\n\n"
        for f in failed:
            yield "data: " + json.dumps({"event": "log", "message": f"[Failed Transfer] {f}"}) + "\n\n"
            
        # 4. Cleanup if Move
        if action == "move" and verified:
            yield "data: " + json.dumps({"event": "log", "message": "=== Starting Cleanup ==="}) + "\n\n"
            
            # Delete placeholders
            deleted = resolver.cleanup_sources(verified)
            yield "data: " + json.dumps({"event": "log", "message": f"Deleted {len(deleted)} source placeholders and cleaned up empty folders."}) + "\n\n"

        yield "data: " + json.dumps({"event": "done", "message": "Operation completed successfully!" if not failed else "Operation completed with warnings/errors."}) + "\n\n"

    return Response(generate(), mimetype="text/event-stream")

if __name__ == "__main__":
    print("Starting Placeholder-Rsync-Resolver Web Server...")
    print("Open http://localhost:5000 in your browser.")
    app.run(host="127.0.0.1", port=5000, debug=True)
