#!/usr/bin/env python3
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from segregator import SegregatorEngine

class SegregatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows Segregation Utility")
        self.root.geometry("800x600")
        self.root.minimum_size = (700, 500)
        
        # Target directory state
        self.target_path = tk.StringVar(value=os.getcwd())
        self.include_binaries = tk.BooleanVar(value=False)
        self.found_items = {"directories": [], "files": []}
        
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        # Configure colors (Sleek Dark Theme)
        self.bg_color = "#1e1e2e"
        self.card_bg = "#252538"
        self.accent_color = "#89b4fa"
        self.accent_hover = "#b4befe"
        self.text_color = "#cdd6f4"
        self.text_muted = "#a6adc8"
        self.border_color = "#313244"
        
        self.root.configure(bg=self.bg_color)
        
        # Ttk style mapping
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Configure standard layouts
        self.style.configure(".", bg=self.bg_color, fg=self.text_color)
        
        # Frames
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("Card.TFrame", background=self.card_bg, borderwidth=1, relief="solid")
        
        # Labels
        self.style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        self.style.configure("Card.TLabel", background=self.card_bg, foreground=self.text_color, font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", background=self.bg_color, foreground=self.accent_color, font=("Segoe UI", 16, "bold"))
        self.style.configure("Title.TLabel", background=self.card_bg, foreground=self.accent_color, font=("Segoe UI", 12, "bold"))
        
        # Buttons
        self.style.configure(
            "TButton", 
            background=self.border_color, 
            foreground=self.text_color, 
            borderwidth=0, 
            font=("Segoe UI", 10, "bold"),
            padding=(10, 5)
        )
        self.style.map(
            "TButton",
            background=[("active", self.card_bg), ("pressed", self.bg_color)],
            foreground=[("active", self.accent_color)]
        )
        
        # Primary Action Button
        self.style.configure(
            "Primary.TButton", 
            background=self.accent_color, 
            foreground=self.bg_color, 
            font=("Segoe UI", 11, "bold"),
            padding=(15, 8)
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", self.accent_hover), ("pressed", self.accent_color)],
            foreground=[("active", self.bg_color)]
        )
        
        # Checkbutton
        self.style.configure(
            "TCheckbutton", 
            background=self.bg_color, 
            foreground=self.text_color, 
            font=("Segoe UI", 10)
        )
        self.style.map(
            "TCheckbutton",
            background=[("active", self.bg_color)],
            foreground=[("active", self.accent_color)]
        )

        # Entry
        self.style.configure(
            "TEntry", 
            fieldbackground=self.card_bg, 
            foreground=self.text_color, 
            bordercolor=self.border_color,
            lightcolor=self.border_color,
            darkcolor=self.border_color,
            insertcolor=self.text_color
        )
        
        # Treeview styling
        self.style.configure(
            "Treeview", 
            background=self.card_bg, 
            fieldbackground=self.card_bg, 
            foreground=self.text_color,
            bordercolor=self.border_color,
            rowheight=25,
            font=("Segoe UI", 9)
        )
        self.style.configure("Treeview.Heading", background=self.border_color, foreground=self.text_color, font=("Segoe UI", 10, "bold"))
        self.style.map(
            "Treeview",
            background=[("selected", self.accent_color)],
            foreground=[("selected", self.bg_color)]
        )

    def create_widgets(self):
        # Main container
        main_container = ttk.Frame(self.root, padding=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header / Title block
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(header_frame, text="Windows Segregator", style="Header.TLabel")
        title_label.pack(side=tk.LEFT)
        
        version_label = ttk.Label(header_frame, text="v1.0", foreground=self.text_muted, font=("Segoe UI", 10, "italic"))
        version_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Directory Selection Card
        dir_card = ttk.Frame(main_container, style="Card.TFrame", padding=15)
        dir_card.pack(fill=tk.X, pady=(0, 15))
        
        dir_label = ttk.Label(dir_card, text="Target Directory to Scan & Segregate", style="Title.TLabel")
        dir_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        dir_entry = ttk.Entry(dir_card, textvariable=self.target_path, width=60)
        dir_entry.grid(row=1, column=0, sticky=tk.EW, padx=(0, 10))
        dir_card.columnconfigure(0, weight=1)
        
        browse_btn = ttk.Button(dir_card, text="Browse...", command=self.browse_directory)
        browse_btn.grid(row=1, column=1)
        
        # Options and Scanning controls
        options_frame = ttk.Frame(main_container)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        bin_check = ttk.Checkbutton(
            options_frame, 
            text="Include Windows executable binaries (.exe, .dll)", 
            variable=self.include_binaries
        )
        bin_check.pack(side=tk.LEFT, py=5)
        
        scan_btn = ttk.Button(options_frame, text="Scan Directory", command=self.scan_directory)
        scan_btn.pack(side=tk.RIGHT)
        
        # Results Listing Card
        results_card = ttk.Frame(main_container, style="Card.TFrame", padding=10)
        results_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        results_title = ttk.Label(results_card, text="Scan Results (Windows-Only Items Found)", style="Title.TLabel")
        results_title.pack(anchor=tk.W, pady=(0, 5))
        
        # Treeview Scrollbar
        tree_scroll = ttk.Scrollbar(results_card)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview list
        self.tree = ttk.Treeview(
            results_card, 
            columns=("Type", "Relative Path"), 
            show="headings", 
            yscrollcommand=tree_scroll.set
        )
        self.tree.heading("Type", text="Type", anchor=tk.W)
        self.tree.heading("Relative Path", text="Relative Path", anchor=tk.W)
        self.tree.column("Type", width=100, minwidth=100, stretch=tk.NO)
        self.tree.column("Relative Path", width=500, minwidth=300, stretch=tk.YES)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        tree_scroll.config(command=self.tree.yview)
        
        # Action Bar (Footer)
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(footer_frame, text="Ready to scan.", foreground=self.text_muted)
        self.status_label.pack(side=tk.LEFT, pady=5)
        
        self.segregate_btn = ttk.Button(
            footer_frame, 
            text="Segregate Items", 
            style="Primary.TButton", 
            command=self.segregate_items,
            state=tk.DISABLED
        )
        self.segregate_btn.pack(side=tk.RIGHT)

    def browse_directory(self):
        selected = filedialog.askdirectory(initialdir=self.target_path.get())
        if selected:
            self.target_path.set(selected)

    def scan_directory(self):
        target = Path(self.target_path.get()).resolve()
        if not target.exists():
            messagebox.showerror("Error", f"Target directory does not exist:\n{target}")
            return
            
        self.status_label.config(text="Scanning...")
        self.root.update_idletasks()
        
        engine = SegregatorEngine(target)
        self.found_items = engine.scan(include_binaries=self.include_binaries.get())
        
        # Clear Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        total_dirs = len(self.found_items["directories"])
        total_files = len(self.found_items["files"])
        
        # Insert Directories
        for d in self.found_items["directories"]:
            self.tree.insert("", tk.END, values=("Directory", str(d.relative_to(target))))
            
        # Insert Files
        for f in self.found_items["files"]:
            self.tree.insert("", tk.END, values=("File", str(f.relative_to(target))))
            
        # Update Status & Button
        if total_dirs == 0 and total_files == 0:
            self.status_label.config(text="Scan complete. No Windows-only items found.")
            self.segregate_btn.config(state=tk.DISABLED)
        else:
            self.status_label.config(text=f"Scan complete. Found {total_dirs} directories and {total_files} files.")
            self.segregate_btn.config(state=tk.NORMAL)

    def segregate_items(self):
        target = Path(self.target_path.get()).resolve()
        total_dirs = len(self.found_items["directories"])
        total_files = len(self.found_items["files"])
        
        if total_dirs == 0 and total_files == 0:
            return
            
        confirm = messagebox.askyesno(
            "Confirm Segregation",
            f"Are you sure you want to move {total_dirs} directories and {total_files} files "
            f"to a new 'Windows' subfolder inside:\n{target}?"
        )
        
        if confirm:
            self.status_label.config(text="Moving files...")
            self.root.update_idletasks()
            
            engine = SegregatorEngine(target)
            results = engine.segregate(self.found_items)
            
            # Re-scan to clear/update
            self.scan_directory()
            
            # Display results summary
            err_count = len(results["errors"])
            success_msg = f"Segregation Complete!\n\nMoved {len(results['moved_directories'])} directories\nMoved {len(results['moved_files'])} files"
            if err_count > 0:
                success_msg += f"\n\nFailed to move {err_count} items (check write permissions)."
                messagebox.showwarning("Complete with Warnings", success_msg)
            else:
                messagebox.showinfo("Success", success_msg)

def main():
    root = tk.Tk()
    app = SegregatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
