#!/usr/bin/env python3
import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from resolver import PlaceholderResolver

class ResolverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Placeholder-Rsync-Resolver")
        self.root.geometry("850x650")
        self.root.minimum_size = (750, 550)

        # Settings variables
        self.placeholder_dir = tk.StringVar(value=os.getcwd())
        self.actual_source = tk.StringVar()
        self.destination_dir = tk.StringVar()
        self.action_mode = tk.StringVar(value="copy")
        self.force_all = tk.BooleanVar(value=False)
        
        # Config Path
        self.config_path = Path(__file__).resolve().parent / "config.json"
        self.load_config()

        # State
        self.scan_data = {"placeholders": [], "local_full": []}
        self.is_processing = False

        self.setup_styles()
        self.create_widgets()

    def load_config(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config = json.load(f)
                    self.placeholder_dir.set(config.get("placeholder_dir", os.getcwd()))
                    self.actual_source.set(config.get("actual_source", ""))
                    self.destination_dir.set(config.get("destination_dir", ""))
                    self.action_mode.set(config.get("action_mode", "copy"))
                    self.force_all.set(config.get("force_all", False))
            except Exception:
                pass

    def save_config(self):
        config = {
            "placeholder_dir": self.placeholder_dir.get(),
            "actual_source": self.actual_source.get(),
            "destination_dir": self.destination_dir.get(),
            "action_mode": self.action_mode.get(),
            "force_all": self.force_all.get()
        }
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    def setup_styles(self):
        # Sleek Dark Palette
        self.bg_color = "#12131a"
        self.card_bg = "#1b1d28"
        self.accent_color = "#a6e3a1" # Success green
        self.accent_hover = "#89b4fa"
        self.text_color = "#cdd6f4"
        self.text_muted = "#7f849c"
        self.border_color = "#313244"
        
        self.root.configure(bg=self.bg_color)
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure(".", bg=self.bg_color, fg=self.text_color)
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("Card.TFrame", background=self.card_bg, borderwidth=1, relief="solid")
        
        self.style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        self.style.configure("Card.TLabel", background=self.card_bg, foreground=self.text_color, font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", background=self.bg_color, foreground=self.accent_color, font=("Segoe UI", 16, "bold"))
        self.style.configure("Title.TLabel", background=self.card_bg, foreground=self.accent_color, font=("Segoe UI", 11, "bold"))
        
        self.style.configure("TButton", background=self.border_color, foreground=self.text_color, borderwidth=0, font=("Segoe UI", 10, "bold"), padding=(10, 5))
        self.style.map("TButton", background=[("active", self.card_bg)], foreground=[("active", self.accent_color)])
        
        self.style.configure("Primary.TButton", background=self.accent_color, foreground=self.bg_color, font=("Segoe UI", 11, "bold"), padding=(15, 8))
        self.style.map("Primary.TButton", background=[("active", self.accent_hover)], foreground=[("active", self.bg_color)])
        
        self.style.configure("TRadiobutton", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        self.style.map("TRadiobutton", background=[("active", self.bg_color)], foreground=[("active", self.accent_color)])
        
        self.style.configure("TCheckbutton", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        self.style.map("TCheckbutton", background=[("active", self.bg_color)], foreground=[("active", self.accent_color)])
        
        self.style.configure("TEntry", fieldbackground=self.card_bg, foreground=self.text_color, bordercolor=self.border_color, insertcolor=self.text_color)
        
        self.style.configure("Treeview", background=self.card_bg, fieldbackground=self.card_bg, foreground=self.text_color, rowheight=24)
        self.style.configure("Treeview.Heading", background=self.border_color, foreground=self.text_color, font=("Segoe UI", 9, "bold"))
        self.style.map("Treeview", background=[("selected", self.accent_color)], foreground=[("selected", self.bg_color)])

    def create_widgets(self):
        main_container = ttk.Frame(self.root, padding=20)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Frame(main_container)
        header.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(header, text="Placeholder Rsync Resolver", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(header, text="v1.0", foreground=self.text_muted, font=("Segoe UI", 10, "italic")).pack(side=tk.LEFT, padx=10, pady=5)

        # Config Panel (Left side) and Files View (Right side)
        paned = ttk.Panedwindow(main_container, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left Config Frame
        left_frame = ttk.Frame(paned, padding=(0, 0, 10, 0))
        paned.add(left_frame, weight=1)

        # Card: Directories
        dir_card = ttk.Frame(left_frame, style="Card.TFrame", padding=15)
        dir_card.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(dir_card, text="Directory Configuration", style="Title.TLabel").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # 1. Placeholder Src
        ttk.Label(dir_card, text="Placeholder Src Dir:", style="Card.TLabel").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_card, textvariable=self.placeholder_dir, width=30).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(dir_card, text="Browse", command=self.browse_placeholder_dir).grid(row=1, column=2, pady=5)

        # 2. Actual Source
        ttk.Label(dir_card, text="Actual Source (Local/Remote):", style="Card.TLabel").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_card, textvariable=self.actual_source, width=30).grid(row=2, column=1, columnspan=2, sticky=tk.EW, padx=5, pady=5)

        # 3. Destination
        ttk.Label(dir_card, text="Destination Dir:", style="Card.TLabel").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_card, textvariable=self.destination_dir, width=30).grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(dir_card, text="Browse", command=self.browse_destination_dir).grid(row=3, column=2, pady=5)
        
        dir_card.columnconfigure(1, weight=1)

        # Card: Options
        opt_card = ttk.Frame(left_frame, style="Card.TFrame", padding=15)
        opt_card.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(opt_card, text="Operation Rules", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        # Action Mode Radio buttons
        radio_frame = ttk.Frame(opt_card)
        radio_frame.pack(fill=tk.X, pady=5)
        ttk.Label(radio_frame, text="Action Mode:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(radio_frame, text="Copy (Safe)", variable=self.action_mode, value="copy").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(radio_frame, text="Move (Delete Src)", variable=self.action_mode, value="move").pack(side=tk.LEFT, padx=10)
        
        # Force all files checkbox
        ttk.Checkbutton(
            opt_card, 
            text="Force rsync for all files (bypass local checks)", 
            variable=self.force_all
        ).pack(anchor=tk.W, pady=10)

        # Buttons
        scan_btn = ttk.Button(left_frame, text="Scan Directory", command=self.scan_directory)
        scan_btn.pack(fill=tk.X, pady=5)

        self.resolve_btn = ttk.Button(
            left_frame, 
            text="Resolve Placeholders", 
            style="Primary.TButton", 
            command=self.start_resolve_thread,
            state=tk.DISABLED
        )
        self.resolve_btn.pack(fill=tk.X, pady=10)

        # Log Card
        log_card = ttk.Frame(left_frame, style="Card.TFrame", padding=10)
        log_card.pack(fill=tk.BOTH, expand=True)
        ttk.Label(log_card, text="Rsync Terminal Logs", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        self.log_text = tk.Text(log_card, bg="#0b0c10", fg="#cdd6f4", font=("Consolas", 9), wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # Right Files Frame
        right_frame = ttk.Frame(paned, padding=(10, 0, 0, 0))
        paned.add(right_frame, weight=1)

        # Treeview
        tree_label = ttk.Label(right_frame, text="Scanned Items to Process", font=("Segoe UI", 11, "bold"))
        tree_label.pack(anchor=tk.W, pady=(0, 5))

        tree_scroll = ttk.Scrollbar(right_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(right_frame, columns=("Type", "Relative Path"), show="headings", yscrollcommand=tree_scroll.set)
        self.tree.heading("Type", text="Type", anchor=tk.W)
        self.tree.heading("Relative Path", text="Relative Path", anchor=tk.W)
        self.tree.column("Type", width=110, stretch=tk.NO)
        self.tree.column("Relative Path", width=250, stretch=tk.YES)
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)

        # Status Bar
        self.status_label = ttk.Label(main_container, text="Ready.", foreground=self.text_muted)
        self.status_label.pack(anchor=tk.W, pady=(10, 0))

    def browse_placeholder_dir(self):
        selected = filedialog.askdirectory(initialdir=self.placeholder_dir.get())
        if selected:
            self.placeholder_dir.set(selected)
            self.save_config()

    def browse_destination_dir(self):
        selected = filedialog.askdirectory(initialdir=self.destination_dir.get())
        if selected:
            self.destination_dir.set(selected)
            self.save_config()

    def scan_directory(self):
        src = Path(self.placeholder_dir.get()).resolve()
        if not src.exists():
            messagebox.showerror("Error", "Placeholder directory does not exist.")
            return

        # Save config settings
        self.save_config()

        self.status_label.config(text="Scanning...")
        self.root.update_idletasks()

        resolver = PlaceholderResolver(src, self.actual_source.get(), self.destination_dir.get())
        self.scan_data = resolver.scan(force_all=self.force_all.get())

        # Clear Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        placeholders = self.scan_data["placeholders"]
        local_full = self.scan_data["local_full"]

        for p in placeholders:
            self.tree.insert("", tk.END, values=("Placeholder (Rsync)", p))
        for l in local_full:
            self.tree.insert("", tk.END, values=("Local Full (Copy)", l))

        total = len(placeholders) + len(local_full)
        if total == 0:
            self.status_label.config(text="Scan finished. No files found.")
            self.resolve_btn.config(state=tk.DISABLED)
        else:
            self.status_label.config(text=f"Scan finished. Found {len(placeholders)} placeholders and {len(local_full)} local files.")
            self.resolve_btn.config(state=tk.NORMAL)

    def append_log(self, text):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_resolve_thread(self):
        src = Path(self.placeholder_dir.get()).resolve()
        dest = Path(self.destination_dir.get()).resolve()
        actual = self.actual_source.get().strip()

        if not dest:
            messagebox.showerror("Error", "Please select a destination directory.")
            return
        if not actual:
            messagebox.showerror("Error", "Please specify the actual source (local path or remote like user@host:path).")
            return

        # Save config settings
        self.save_config()

        total_placeholders = len(self.scan_data["placeholders"])
        total_local = len(self.scan_data["local_full"])

        confirm = messagebox.askyesno(
            "Confirm Resolution",
            f"Are you sure you want to perform the {self.action_mode.get().upper()} operation?\n\n"
            f"Transferring {total_placeholders} placeholders and {total_local} local files\n"
            f"To: {dest}"
        )
        if not confirm:
            return

        # Start background thread to keep GUI responsive
        self.is_processing = True
        self.resolve_btn.config(state=tk.DISABLED)
        self.clear_logs()
        
        threading.Thread(target=self.run_resolution, args=(src, actual, dest), daemon=True).start()

    def run_resolution(self, src, actual, dest):
        resolver = PlaceholderResolver(src, actual, dest)
        placeholders = self.scan_data["placeholders"]
        local_full = self.scan_data["local_full"]

        # 1. Local copy
        copied = []
        if local_full:
            self.status_label.config(text="Copying local files...")
            self.append_log("=== Starting Local Copy ===")
            
            def local_callback(msg):
                self.append_log(msg)
                self.status_label.config(text=msg)
                
            copied, failed_copies = resolver.run_local_copy(local_full, progress_callback=local_callback)
            self.append_log(f"Local copies finished: {len(copied)} succeeded, {len(failed_copies)} failed.\n")

        # 2. Rsync fetch
        rsync_success = True
        if placeholders:
            self.status_label.config(text="Fetching placeholders via rsync...")
            self.append_log("=== Starting Rsync Fetch ===")
            
            def rsync_callback(line):
                self.append_log(line)
                
            rsync_success, msg = resolver.run_rsync(placeholders, progress_callback=rsync_callback)
            if rsync_success:
                self.append_log("\n[Rsync] Completed successfully.\n")
            else:
                self.append_log(f"\n[Rsync Error] {msg}\n")

        # 3. Verification
        self.status_label.config(text="Verifying transfers...")
        self.append_log("=== Verifying Transfer Integrity ===")
        
        all_targets = placeholders + local_full
        verified, failed = resolver.verify_transfers(all_targets)
        
        self.append_log(f"Verification results:")
        self.append_log(f"  - Successfully verified files: {len(verified)}")
        self.append_log(f"  - Failed/Missing files: {len(failed)}")
        for f in failed:
            self.append_log(f"    [FAILED] {f}")
        self.append_log("")

        # 4. Cleanup if Move
        if self.action_mode.get() == "move" and verified:
            self.status_label.config(text="Cleaning up placeholders...")
            self.append_log("=== Cleaning Up Source Placeholders ===")
            
            deleted = resolver.cleanup_sources(verified, progress_callback=lambda msg: self.append_log(msg))
            self.append_log(f"Deleted {len(deleted)} source files and cleared empty directories.\n")

        self.append_log("=== Operation Complete ===")
        self.status_label.config(text="Operation complete.")
        
        # Finished
        self.is_processing = False
        
        # Trigger rescan on main thread
        self.root.after(0, self.scan_directory)
        
        # Alert dialog
        msg = f"Resolution finished!\n\nSuccessfully verified: {len(verified)} files."
        if failed:
            msg += f"\nFailed to transfer: {len(failed)} files (check logs for details)."
            messagebox.showwarning("Complete with Errors", msg)
        else:
            messagebox.showinfo("Success", msg)

def main():
    root = tk.Tk()
    app = ResolverGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
