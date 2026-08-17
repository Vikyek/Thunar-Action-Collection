#!/usr/bin/env python3
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from dedup import DeduplicatorEngine

class DedupGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Deduplicate & Clean Utility")
        self.root.geometry("800x600")
        self.root.minimum_size = (700, 500)

        # Variables
        self.target_dir = tk.StringVar(value=os.getcwd())
        self.no_rename = tk.BooleanVar(value=False)
        self.no_win_clean = tk.BooleanVar(value=False)
        self.dry_run = tk.BooleanVar(value=False)

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        # Sleek dark palette
        self.bg_color = "#151515"
        self.card_bg = "#1f1f1f"
        self.accent_color = "#eba0ac" # Pinkish Red accent
        self.accent_hover = "#f38ba8"
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
        
        self.style.configure("TCheckbutton", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        self.style.map("TCheckbutton", background=[("active", self.bg_color)], foreground=[("active", self.accent_color)])
        
        self.style.configure("TEntry", fieldbackground=self.card_bg, foreground=self.text_color, bordercolor=self.border_color, insertcolor=self.text_color)

    def create_widgets(self):
        main_container = ttk.Frame(self.root, padding=20)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Header
        header = ttk.Frame(main_container)
        header.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(header, text="Deduplication & Cleanup", style="Header.TLabel").pack(side=tk.LEFT)
        ttk.Label(header, text="v1.0", foreground=self.text_muted, font=("Segoe UI", 10, "italic")).pack(side=tk.LEFT, padx=10, pady=5)

        # Directory Card
        dir_card = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        dir_card.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(dir_card, text="Target Path", style="Title.TLabel").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        ttk.Label(dir_card, text="Directory to clean:", style="Card.TLabel").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_card, textvariable=self.target_dir, width=50).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(dir_card, text="Browse...", command=self.browse_dir).grid(row=1, column=2, pady=5)
        dir_card.columnconfigure(1, weight=1)

        # Options Card
        opt_card = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        opt_card.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(opt_card, text="Execution Settings", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 10))

        cb_frame = ttk.Frame(opt_card)
        cb_frame.pack(fill=tk.X)
        
        # Invert checkboxes so they match CLI options --no-rename/--no-win-clean but read intuitively in GUI
        self.rename_var = tk.BooleanVar(value=True)
        self.winclean_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(cb_frame, text="Rename Copy Suffixes (e.g. removes '- Copy' tags)", variable=self.rename_var).pack(side=tk.LEFT, padx=15)
        ttk.Checkbutton(cb_frame, text="Delete Windows leftovers (desktop.ini, thumbs.db, etc.)", variable=self.winclean_var).pack(side=tk.LEFT, padx=15)
        ttk.Checkbutton(cb_frame, text="Simulation Mode (Dry Run)", variable=self.dry_run).pack(side=tk.LEFT, padx=15)

        # Action Buttons
        self.run_btn = ttk.Button(main_container, text="Run Deduplication & Cleanup", style="Primary.TButton", command=self.start_dedup_thread)
        self.run_btn.pack(fill=tk.X, pady=5)

        # Logs View
        log_card = ttk.Frame(main_container, style="Card.TFrame", padding=12)
        log_card.pack(fill=tk.BOTH, expand=True, pady=10)
        ttk.Label(log_card, text="Console output", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 5))

        self.log_text = tk.Text(log_card, bg="#0c0c0c", fg="#cdd6f4", font=("Consolas", 9), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

        # Status Bar
        self.status_label = ttk.Label(main_container, text="Ready.", foreground=self.text_muted)
        self.status_label.pack(anchor=tk.W)

    def browse_dir(self):
        selected = filedialog.askdirectory(initialdir=self.target_dir.get())
        if selected:
            self.target_dir.set(selected)

    def append_log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_dedup_thread(self):
        target = Path(self.target_dir.get()).resolve()
        if not target.exists() or not target.is_dir():
            messagebox.showerror("Error", "Target path does not exist or is not a directory.")
            return

        confirm = messagebox.askyesno(
            "Confirm Deduplication",
            f"Are you sure you want to run deduplication and clean empty files/dirs inside:\n{target}?"
        )
        if not confirm:
            return

        self.run_btn.config(state=tk.DISABLED)
        self.clear_logs()
        self.status_label.config(text="Processing...")
        
        threading.Thread(target=self.run_deduplication, args=(target,), daemon=True).start()

    def run_deduplication(self, target):
        engine = DeduplicatorEngine([target])
        
        def gui_callback(pct, msg):
            self.append_log(f"[{pct}%] {msg}")
            self.status_label.config(text=msg)
            self.root.update_idletasks()

        results = engine.run_deduplication(
            no_rename=not self.rename_var.get(),
            no_win_clean=not self.winclean_var.get(),
            progress_callback=gui_callback,
            dry_run=self.dry_run.get()
        )

        saved_mb = results["saved_space_bytes"] / 1024 / 1024

        self.append_log("\n=== Execution Summary ===")
        self.append_log(f"• Files scanned: {results['scanned_files']}")
        self.append_log(f"• Empty files deleted: {len(results['empty_deleted'])}")
        self.append_log(f"• Duplicate files deleted: {len(results['duplicates_deleted'])}")
        self.append_log(f"• Copy suffixes renamed: {len(results['renamed_files'])}")
        self.append_log(f"• Windows system leftovers cleaned: {len(results['win_leftovers_deleted'])}")
        self.append_log(f"• Empty folders deleted: {len(results['empty_dirs_deleted'])}")
        self.append_log(f"• Reclaimed Disk Space: {saved_mb:.2f} MB")
        self.append_log("=== Process Complete ===")

        self.status_label.config(text="Deduplication finished.")
        self.run_btn.config(state=tk.NORMAL)

        summary_msg = f"Deduplication complete!\n\nReclaimed Disk Space: {saved_mb:.2f} MB\nDuplicates deleted: {len(results['duplicates_deleted'])}"
        messagebox.showinfo("Success", summary_msg)

def main():
    root = tk.Tk()
    app = DedupGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
