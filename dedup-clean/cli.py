#!/usr/bin/env python3
import argparse
import sys
import json
import subprocess
import time
from pathlib import Path
from dedup import DeduplicatorEngine

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
    parser = argparse.ArgumentParser(description="Deduplicate files, clean empty files/dirs, and clean names.")
    parser.add_argument("directories", nargs="*", help="Directories to process")
    parser.add_argument("--no-rename", action="store_true", help="Disable renaming of ' - Copy' files")
    parser.add_argument("--no-win-clean", action="store_true", help="Disable cleanup of Windows leftover files/dirs")
    parser.add_argument("-d", "--dry-run", action="store_true", help="Perform a dry run (no changes made)")
    parser.add_argument("-j", "--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--notify", action="store_true", help="Enable desktop notifications (non-interactive mode)")

    try:
        args = parser.parse_args()
    except SystemExit as e:
        if e.code == 0:
            sys.exit(0)
        # Notify if args failed
        update_notif(None, "Deduplication Error", "Invalid arguments provided.", icon="dialog-error")
        sys.exit(1)

    target_dirs = args.directories if args.directories else ["."]
    
    # Resolve target directories
    directories = []
    for d in target_dirs:
        p = Path(d).resolve()
        if p.exists() and p.is_dir():
            directories.append(p)

    if not directories:
        if args.notify:
            update_notif(None, "Deduplication Error", "No valid directories provided.", icon="dialog-error")
        else:
            print("Error: No valid directories provided.", file=sys.stderr)
        sys.exit(1)

    # Human readable names for notification
    names = [d.name for d in directories]
    if len(names) == 1:
        target_desc = f"Folder: '{names[0]}'"
    else:
        target_desc = f"Folders: {', '.join([f'\'{n}\'' for n in names[:3]])}" + ("..." if len(names) > 3 else "")

    # Notify Mode Flow
    if args.notify:
        notif_id = update_notif(None, "Deduplication & Cleanup", f"{target_desc}\nInitializing file scan...", progress=0, icon="edit-delete")
        
        engine = DeduplicatorEngine(directories)
        
        last_update = time.time()
        def progress_callback(pct, msg):
            nonlocal last_update, notif_id
            now = time.time()
            # Throttle notifications
            if pct == 100 or now - last_update > 0.35:
                notif_id = update_notif(notif_id, "Deduplication & Cleanup", f"{target_desc}\n{msg}", progress=pct, icon="edit-delete")
                last_update = now

        results = engine.run_deduplication(
            no_rename=args.no_rename, 
            no_win_clean=args.no_win_clean, 
            progress_callback=progress_callback,
            dry_run=args.dry_run
        )
        
        # Display final result summary
        saved_mb = results["saved_space_bytes"] / 1024 / 1024
        
        msg = f"{target_desc}\n\n"
        if args.dry_run:
            msg += "[DRY RUN] Summary:\n"
        msg += f"• Empty files deleted: {len(results['empty_deleted'])}\n"
        msg += f"• Duplicate files deleted: {len(results['duplicates_deleted'])}\n"
        if not args.no_rename:
            msg += f"• Files renamed: {len(results['renamed_files'])}\n"
        if not args.no_win_clean:
            msg += f"• Windows leftovers deleted: {len(results['win_leftovers_deleted'])}\n"
        msg += f"• Empty directories deleted: {len(results['empty_dirs_deleted'])}\n"
        msg += f"• Disk space saved: {saved_mb:.2f} MB"
        
        update_notif(notif_id, "Deduplication & Cleanup Complete", msg, progress=100, icon="dialog-ok")
        sys.exit(0)

    # JSON Mode Flow
    if args.json:
        engine = DeduplicatorEngine(directories)
        results = engine.run_deduplication(
            no_rename=args.no_rename, 
            no_win_clean=args.no_win_clean,
            dry_run=args.dry_run
        )
        # Convert Path objects to string lists for JSON
        output = {
            "directories": [str(d) for d in directories],
            "dry_run": args.dry_run,
            "scanned_files": results["scanned_files"],
            "empty_deleted": results["empty_deleted"],
            "win_leftovers": results["win_leftovers_deleted"],
            "duplicates_deleted": results["duplicates_deleted"],
            "renamed_files": results["renamed_files"],
            "empty_dirs_deleted": [str(d) for d in results["empty_dirs_deleted"]],
            "saved_space_mb": results["saved_space_bytes"] / 1024 / 1024
        }
        print(json.dumps(output, indent=2))
        sys.exit(0)

    # Interactive Terminal Flow
    engine = DeduplicatorEngine(directories)
    print("=" * 60)
    print(" Deduplication & Cleanup CLI")
    print(f" Targets      : {', '.join([str(d) for d in directories])}")
    print(f" Options      : Rename={not args.no_rename}, WinClean={not args.no_win_clean}")
    print(f" Mode         : {'DRY RUN (Trial)' if args.dry_run else 'ACTIVE CLEANUP'}")
    print("=" * 60)

    print("Running scan and deduplication analysis...")
    
    # Progress callback prints dots
    def cli_progress(pct, msg):
        print(f"[{pct}%] {msg}")

    results = engine.run_deduplication(
        no_rename=args.no_rename, 
        no_win_clean=args.no_win_clean, 
        progress_callback=cli_progress,
        dry_run=args.dry_run
    )
    
    saved_mb = results["saved_space_bytes"] / 1024 / 1024
    
    print("\n" + "-" * 40)
    print("Cleanup Summary:")
    print(f"  - Files Scanned: {results['scanned_files']}")
    print(f"  - Empty Files Deleted: {len(results['empty_deleted'])}")
    print(f"  - Duplicate Files Deleted: {len(results['duplicates_deleted'])}")
    print(f"  - Copy Suffixes Renamed: {len(results['renamed_files'])}")
    print(f"  - Windows System Leftovers Cleaned: {len(results['win_leftovers_deleted'])}")
    print(f"  - Empty Directories Removed: {len(results['empty_dirs_deleted'])}")
    print(f"  - Total Disk Space Reclaimed: {saved_mb:.2f} MB")
    print("-" * 40)

if __name__ == "__main__":
    main()
