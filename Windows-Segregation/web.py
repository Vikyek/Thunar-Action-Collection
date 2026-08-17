#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request, render_template, send_from_directory

# Add the root folder to the python path to load the segregator module
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from segregator import SegregatorEngine, DEFAULT_CONFIG

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route("/")
def index():
    default_dir = os.getcwd()
    return render_template("index.html", default_dir=default_dir)

@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json() or {}
    target_dir = data.get("directory", "")
    include_binaries = data.get("include_binaries", False)
    
    if not target_dir:
        return jsonify({"success": False, "error": "Directory path is required"}), 400
        
    path = Path(target_dir).resolve()
    if not path.exists() or not path.is_dir():
        return jsonify({"success": False, "error": "Directory does not exist or is not a folder"}), 400
        
    try:
        engine = SegregatorEngine(path)
        found = engine.scan(include_binaries=include_binaries)
        
        # Return scanned items as relative strings
        return jsonify({
            "success": True,
            "directory": str(path),
            "directories": [str(d.relative_to(path)) for d in found["directories"]],
            "files": [str(f.relative_to(path)) for f in found["files"]]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/segregate", methods=["POST"])
def api_segregate():
    data = request.get_json() or {}
    target_dir = data.get("directory", "")
    include_binaries = data.get("include_binaries", False)
    dry_run = data.get("dry_run", False)
    
    if not target_dir:
        return jsonify({"success": False, "error": "Directory path is required"}), 400
        
    path = Path(target_dir).resolve()
    if not path.exists() or not path.is_dir():
        return jsonify({"success": False, "error": "Directory does not exist"}), 400
        
    try:
        engine = SegregatorEngine(path)
        # Scan again to ensure list is fresh
        found = engine.scan(include_binaries=include_binaries)
        
        results = engine.segregate(found, dry_run=dry_run)
        
        return jsonify({
            "success": True,
            "dry_run": dry_run,
            "results": results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    # Start on port 5000 by default
    print("Starting Windows-Segregation Web Server...")
    print("Open http://localhost:5000 in your browser.")
    app.run(host="127.0.0.1", port=5000, debug=True)
