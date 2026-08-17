#!/usr/bin/env python3
import argparse
import sys
import json
import subprocess
import time
from pathlib import Path
from segregator import SegregatorEngine

def update_notif(notif_id, title, message, progress=None, icon="dialog-information"):
    cmd = ["notify-send", title, message, "-i", icon]
    if notif_id is not None:
        cmd += ["-r", str(notif_id)]
    if progress is not None:
        cmd += ["-h", f"int:value:{progress}"]
    if notif_id is None:
        cmd += ["-p"]
        
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        if notif_id is None:
            return int(res.stdout.strip())
    except Exception:
        pass
    return notif_id

def main():
    parser = argparse.ArgumentParser(
        description="Scan a directory recursively, identify Windows-only files and folders, and segregate them."
    )
    parser.add_argument(
        "directory", 
        nargs="*", 
        help="The target directory/directories to scan and segregate (default: current directory)"
    )
    parser.add_argument(
        "-b", "--binaries", 
        action="store_true", 
        help="Include compiled Windows binaries (.exe, .dll) in segregation"
    )
    parser.add_argument(
        "-d", "--dry-run", 
        action="store_true", 
        help="Perform a trial run without making any filesystem changes"
    )
    parser.add_argument(
        "-j", "--json", 
        action="store_true", 
        help="Output the results in JSON format"
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Enable desktop notifications (non-interactive mode)"
    )

    args = parser.parse_args()
    
    # Handle multiple directories or default to current
    target_dirs = args.directory if args.directory else ["."]
    
    # If in notify mode, run non-interactively
    if args.notify:
        notif_id = None
        # Normalize targets
        resolved_dirs = []
        for d in target_dirs:
            p = Path(d).resolve()
            if p.exists() and p.is_dir():
                resolved_dirs.append(p)
                
        if not resolved_dirs:
            update_notif(None, "Windows Segregation", "No valid target directories provided.", icon="dialog-error")
            sys.exit(1)
            
        desc = ", ".join([d.name for d in resolved_dirs[:3]])
        if len(resolved_dirs) > 3:
            desc += "..."
            
        notif_id = update_notif(None, "Windows Segregation", f"Scanning {desc}...", progress=10, icon="folder-symbolic")
        
        total_moved_dirs = 0
        total_moved_files = 0
        errors = []
        
        for idx, target_path in enumerate(resolved_dirs):
            engine = SegregatorEngine(target_path)
            found_items = engine.scan(include_binaries=args.binaries)
            
            # Progress update (10% - 80%)
            progress = 10 + int((idx / len(resolved_dirs)) * 70)
            update_notif(notif_id, "Windows Segregation", f"Segregating {target_path.name}...", progress=progress, icon="folder-symbolic")
            
            if found_items["directories"] or found_items["files"]:
                results = engine.segregate(found_items, dry_run=args.dry_run)
                total_moved_dirs += len(results["moved_directories"])
                total_moved_files += len(results["moved_files"])
                errors.extend(results["errors"])
                
        # Final notification
        msg = f"Cleaned folders: {desc}\n\n"
        if args.dry_run:
            msg += f"[DRY RUN] Would move:\n"
        else:
            msg += f"Successfully segregated:\n"
        msg += f"• Directories moved: {total_moved_dirs}\n"
        msg += f"• Files moved: {total_moved_files}"
        
        if errors:
            msg += f"\n• Errors encountered: {len(errors)}"
            
        icon = "dialog-ok" if not errors else "dialog-warning"
        update_notif(notif_id, "Windows Segregation Complete", msg, progress=100, icon=icon)
        sys.exit(0)

    # Standard CLI Flow (JSON or Interactive)
    # We will assume a single target directory for simple interactive CLI
    target_path = Path(target_dirs[0]).resolve()

    if not target_path.exists():
        if args.json:
            print(json.dumps({"error": f"Directory does not exist: {target_path}"}))
        else:
            print(f"Error: Target directory does not exist: {target_path}", file=sys.stderr)
        sys.exit(1)

    engine = SegregatorEngine(target_path)
    
    # Scan
    found_items = engine.scan(include_binaries=args.binaries)
    
    # If JSON output is requested
    if args.json:
        results = engine.segregate(found_items, dry_run=args.dry_run)
        output = {
            "target_dir": str(target_path),
            "dry_run": args.dry_run,
            "scanned": {
                "directories": [str(d.relative_to(target_path)) for d in found_items["directories"]],
                "files": [str(f.relative_to(target_path)) for f in found_items["files"]]
            },
            "results": results
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    # Human-readable output
    print("=" * 60)
    print(f" Windows-Segregation CLI Tool")
    print(f" Target Directory: {target_path}")
    print(f" Mode: {'DRY RUN (Trial)' if args.dry_run else 'ACTIVE SEGREGATION'}")
    print("=" * 60)

    total_dirs = len(found_items["directories"])
    total_files = len(found_items["files"])

    if total_dirs == 0 and total_files == 0:
        print("No Windows-only files or directories found.")
        sys.exit(0)

    if total_dirs > 0:
        print(f"\nFound {total_dirs} Windows-only Directories:")
        for d in found_items["directories"]:
            print(f"  [DIR]  {d.relative_to(target_path)}")

    if total_files > 0:
        print(f"\nFound {total_files} Windows-only Files:")
        for f in found_items["files"]:
            print(f"  [FILE] {f.relative_to(target_path)}")

    print("\n" + "-" * 40)
    
    if args.dry_run:
        print(f"Dry run complete. No files were moved.")
    else:
        confirm = input(f"\nAre you sure you want to move these {total_dirs} directories and {total_files} files to '{target_path}/Windows'? (y/N): ")
        if confirm.lower() in ("y", "yes"):
            results = engine.segregate(found_items, dry_run=False)
            
            print(f"\nSuccessfully moved {len(results['moved_directories'])} directories:")
            for src, dest in results["moved_directories"]:
                print(f"  [DIR]  {src} -> Windows/{src}")
                
            print(f"\nSuccessfully moved {len(results['moved_files'])} files:")
            for src, dest in results["moved_files"]:
                print(f"  [FILE] {src} -> Windows/{src}")
                
            if results["errors"]:
                print(f"\nEncountered {len(results['errors'])} errors:")
                for err in results["errors"]:
                    print(f"  [ERR]  {err}")
        else:
            print("Operation cancelled. No changes were made.")

if __name__ == "__main__":
    main()
