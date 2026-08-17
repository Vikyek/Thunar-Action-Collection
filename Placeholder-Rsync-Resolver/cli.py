#!/usr/bin/env python3
import argparse
import sys
import json
import subprocess
from pathlib import Path
from resolver import PlaceholderResolver

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
        description="Scan a directory for 0-byte placeholder files and copy/move the actual files from a source directory (local or remote) using rsync."
    )
    
    parser.add_argument(
        "-s", "--src", 
        help="The source directory containing placeholder/nonsynchronized files"
    )
    parser.add_argument(
        "-a", "--actual", 
        help="The actual source containing the real files (local path or remote like user@host:/path)"
    )
    parser.add_argument(
        "-d", "--dest", 
        help="The destination directory where full files should be placed"
    )
    parser.add_argument(
        "--action", 
        choices=["copy", "move"], 
        default="copy", 
        help="The action to perform: 'copy' or 'move' (default: copy)"
    )
    parser.add_argument(
        "-f", "--force-all", 
        action="store_true", 
        help="Force rsync for all files, even if they are not 0-byte placeholders"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Perform a dry run (simulation only)"
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Enable desktop notifications (non-interactive mode)"
    )

    args = parser.parse_args()

    # Load defaults from config.json if present
    script_dir = Path(__file__).resolve().parent
    config_path = script_dir / "config.json"
    config_data = {}
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
        except Exception:
            pass

    # Merge args and config
    src_dir = args.src or config_data.get("placeholder_dir")
    actual_source = args.actual or config_data.get("actual_source")
    dest_dir = args.dest or config_data.get("destination_dir")
    action_mode = args.action if args.action != "copy" else config_data.get("action_mode", "copy")

    if not src_dir:
        if args.notify:
            update_notif(None, "Placeholder Resolver Error", "Source directory not specified.", icon="dialog-error")
        else:
            print("Error: Source directory is required (use -s/--src).", file=sys.stderr)
        sys.exit(1)

    placeholder_path = Path(src_dir).resolve()
    
    if not placeholder_path.exists():
        if args.notify:
            update_notif(None, "Placeholder Resolver Error", f"Source directory does not exist:\n{placeholder_path}", icon="dialog-error")
        else:
            print(f"Error: Source directory does not exist: {placeholder_path}", file=sys.stderr)
        sys.exit(1)

    # Verify actual and dest are provided (either arg or config)
    if not actual_source or not dest_dir:
        if args.notify:
            update_notif(
                None, 
                "Placeholder Resolver Error", 
                "Missing 'actual source' or 'destination' path. Please configure them in the GUI or Web Dashboard first.", 
                icon="dialog-error"
            )
        else:
            print("Error: Actual source and destination directories must be specified (via args or config.json).", file=sys.stderr)
        sys.exit(1)

    dest_path = Path(dest_dir).resolve()

    # If in notify mode
    if args.notify:
        notif_id = update_notif(
            None, 
            "Placeholder Resolver", 
            f"Scanning '{placeholder_path.name}' for placeholders...", 
            progress=10, 
            icon="system-run"
        )
        
        resolver = PlaceholderResolver(placeholder_path, actual_source, dest_path)
        scan_results = resolver.scan(force_all=args.force_all)
        
        placeholders = scan_results["placeholders"]
        local_full = scan_results["local_full"]
        total_files = len(placeholders) + len(local_full)
        
        if total_files == 0:
            update_notif(notif_id, "Placeholder Resolver Complete", "No files found to resolve.", progress=100, icon="dialog-ok")
            sys.exit(0)

        # Update notification for scanning complete
        update_notif(
            notif_id, 
            "Placeholder Resolver", 
            f"Found {len(placeholders)} placeholders & {len(local_full)} local files.\nStarting transfer...", 
            progress=25, 
            icon="system-run"
        )
        
        # 1. Local copy
        copied_successfully = []
        if local_full:
            copied_successfully, failed_copies = resolver.run_local_copy(local_full)
            
        update_notif(
            notif_id, 
            "Placeholder Resolver", 
            f"Copied {len(copied_successfully)} local files.\nRunning rsync fetch...", 
            progress=50, 
            icon="system-run"
        )
        
        # 2. Rsync transfer
        rsync_success = True
        if placeholders:
            rsync_success, msg = resolver.run_rsync(placeholders)
            
        # 3. Verification
        update_notif(notif_id, "Placeholder Resolver", "Verifying transfers...", progress=85, icon="system-run")
        verified_success, failed_verification = resolver.verify_transfers(placeholders + local_full)
        
        # 4. Move Cleanup
        deleted_count = []
        if action_mode == "move" and verified_success:
            deleted_count = resolver.cleanup_sources(verified_success)
            
        # Final notification
        success_count = len(verified_success)
        fail_count = len(failed_verification)
        
        msg = f"Target: '{placeholder_path.name}'\n\n"
        msg += f"• Files verified: {success_count}\n"
        if fail_count > 0:
            msg += f"• Files failed: {fail_count}\n"
        if action_mode == "move":
            msg += f"• Placeholders deleted: {len(deleted_count)}\n"
        
        icon = "dialog-ok" if fail_count == 0 else "dialog-warning"
        update_notif(notif_id, "Placeholder Resolver Complete", msg, progress=100, icon=icon)
        sys.exit(0)

    # Standard Interactive CLI Flow
    resolver = PlaceholderResolver(placeholder_path, actual_source, dest_path)
    
    print("=" * 60)
    print(" Placeholder-Rsync-Resolver CLI")
    print(f" Placeholder Dir : {placeholder_path}")
    print(f" Actual Source   : {actual_source}")
    print(f" Destination Dir : {dest_path}")
    print(f" Action Mode     : {action_mode.upper()}")
    print(f" Operation Type  : {'DRY RUN (Trial)' if args.dry_run else 'ACTIVE RESOLUTION'}")
    print("=" * 60)

    print("Scanning directory for placeholders...")
    scan_results = resolver.scan(force_all=args.force_all)
    
    placeholders = scan_results["placeholders"]
    local_full = scan_results["local_full"]
    total_items = len(placeholders) + len(local_full)
    
    if total_items == 0:
        print("No files found to resolve.")
        sys.exit(0)
        
    print(f"Scan complete:")
    print(f"  - 0-byte Placeholders to fetch via rsync: {len(placeholders)}")
    print(f"  - Local full-size files to copy directly: {len(local_full)}")

    if args.dry_run:
        print("\n[Dry Run] Scanned files list:")
        if placeholders:
            print("\nPlaceholders:")
            for p in placeholders[:10]:
                print(f"  [RSYNC]  {p}")
            if len(placeholders) > 10:
                print(f"  ... and {len(placeholders) - 10} more")
        if local_full:
            print("\nLocal full-size:")
            for l in local_full[:10]:
                print(f"  [COPY]   {l}")
            if len(local_full) > 10:
                print(f"  ... and {len(local_full) - 10} more")
        print("\nDry run completed. No files were transferred.")
        sys.exit(0)

    # Confirmation
    confirm = input(f"\nAre you sure you want to perform this {action_mode} operation? (y/N): ")
    if confirm.lower() not in ("y", "yes"):
        print("Operation cancelled.")
        sys.exit(0)

    # 1. Local copy of already downloaded files
    copied_successfully = []
    if local_full:
        print("\n--- Starting Local File Copies ---")
        copied_successfully, failed_copies = resolver.run_local_copy(
            local_full, 
            progress_callback=print
        )
        print(f"Local copy finished: {len(copied_successfully)} succeeded, {len(failed_copies)} failed.")

    # 2. Rsync transfer of placeholders
    rsync_success = False
    if placeholders:
        print("\n--- Starting Rsync Fetch ---")
        rsync_success, msg = resolver.run_rsync(
            placeholders, 
            progress_callback=print
        )
        if rsync_success:
            print("Rsync fetch completed successfully.")
        else:
            print(f"Rsync fetch failed: {msg}")

    # 3. Verification
    print("\n--- Verifying Transfers ---")
    all_targets = placeholders + local_full
    verified_success, failed_verification = resolver.verify_transfers(all_targets)
    
    print(f"Verification Results:")
    print(f"  - Total files successfully verified: {len(verified_success)}")
    if failed_verification:
        print(f"  - Total files failed to transfer/verify: {len(failed_verification)}")
        for f in failed_verification[:5]:
            print(f"    [FAIL] {f}")
        if len(failed_verification) > 5:
            print(f"    ... and {len(failed_verification) - 5} more")

    # 4. Move Cleanup
    if action_mode == "move" and verified_success:
        print("\n--- Cleaning Up Source Files (Move Mode) ---")
        deleted_count = resolver.cleanup_sources(
            verified_success, 
            progress_callback=print
        )
        print(f"Deleted {len(deleted_count)} source placeholder files and cleaned up empty folders.")

    print("\nOperation completed!")

if __name__ == "__main__":
    main()
