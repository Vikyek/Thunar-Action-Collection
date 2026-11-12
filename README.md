# Thunar Custom Actions Collection

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository acts as a central index and grouping for custom Thunar action scripts and utilities designed to enhance the Thunar File Manager on Linux.

---

## 📋 Requirements & Dependencies

- **File Manager:** `thunar` (XFCE / Linux desktop file manager)
- **Core Runtime:** `python3` (3.8+)
- **System Utilities:**
  - `wl-clipboard` (Wayland clipboard support) or `xclip` (X11 clipboard support)
  - `libnotify` (`notify-send` for desktop alerts)
  - `rsync` (for placeholder synchronization)
  - `exo-utils` (`exo-open` for sudoedit terminal launcher)
- **Optional Python Libraries:**
  - `python-pillow` (for WebP image conversion)
  - `python-flask` (for Web interfaces in dedup/segregator/resolver)
  - `tk` / `python-tkinter` (for desktop GUI interfaces)

Install on Arch Linux:
```bash
sudo pacman -S thunar python rsync libnotify wl-clipboard xclip python-pillow python-flask tk
```

---

## 🚀 Installation & Setup

### Automated Installation
Run the master installer to initialize all submodules and register local CLI wrappers in `~/.local/bin`:
```bash
git clone --recurse-submodules https://github.com/Vikyek/Thunar-Action-Collection.git
cd Thunar-Action-Collection
chmod +x install.sh
./install.sh
```

### Manual Installation & uca.xml Setup
1. Clone the repository and install dependencies.
2. Merge the action configurations below into your Thunar configuration file at `~/.config/Thunar/uca.xml` (or configure each action via Thunar's GUI: **Edit** ➔ **Configure custom actions...**).

---

## 💻 Usage & Actions Overview

Once installed and configured in `~/.config/Thunar/uca.xml`, right-click on any file, folder, or empty background in Thunar to access these actions:

### 1. [Thunar-Paste-Dereference](https://github.com/Vikyek/Thunar-Paste-Dereference)
* **Description:** Pastes copied files/folders from clipboard but dereferences symbolic links, copying the actual targets. Supports both Wayland (`wl-paste`) and X11 (`xclip`).
* **Usage:** Copy symlinks, navigate to destination, right-click background ➔ **Paste (Dereference Links)**.
* **Command:** `thunar-paste-deref %f`

### 2. [Windows-Segregation](https://github.com/Vikyek/Windows-Segregation)
* **Description:** Scans and moves Windows-only system files or directories to a dedicated Windows folder to clean up Linux workspaces.
* **Usage:** Right-click directory ➔ **Segregate Windows Files**.
* **Command:** `windows-segregation --notify %F`

### 3. [Placeholder-Rsync-Resolver](https://github.com/Vikyek/Placeholder-Rsync-Resolver)
* **Description:** Resolves 0-byte placeholder files by downloading their actual content from a remote server using Rsync.
* **Usage:** Right-click folder with placeholders ➔ **Resolve Placeholders (Rsync)**.
* **Command:** `placeholder-rsync-resolver --src %f --notify`

### 4. [dedup-clean](https://github.com/Vikyek/dedup-clean)
* **Description:** Deduplicates files by hash (keeping the oldest version) and cleans up empty files.
* **Usage:** Right-click folder ➔ **Deduplicate & Clean Empty Files**.
* **Command:** `dedup-clean %F`

### 5. [Thunar-Webp-Optimizer](https://github.com/Vikyek/Thunar-Webp-Optimizer)
* **Description:** Converts selected images to the modern WebP format, supporting compression control.
* **Usage:** Select images, right-click ➔ **Convert to WebP**.
* **Command:** `thunar-webp-optimizer %F`

### 6. [Thunar-Symlink-Translator](https://github.com/Vikyek/Thunar-Symlink-Translator)
* **Description:** Translates absolute symlinks in selected folders/files to relative ones to keep them portable across machines.
* **Usage:** Select folder/links, right-click ➔ **Translate Symlinks to Relative**.
* **Command:** `thunar-symlink-translator %F`

### 7. Edit as Administrator (sudoedit)
* **Description:** Securely edits text files with root privileges using your default `$EDITOR` via standard `sudoedit`.
* **Usage:** Right-click text file ➔ **Edit as Administrator (sudoedit)**.
* **Command:** `exo-open --launch TerminalEmulator sudoedit %f`

---

## ⚙️ uca.xml Configuration Reference

These actions are registered in your Thunar configuration (`~/.config/Thunar/uca.xml`). Below is the XML configuration matching this setup:

```xml
<actions>
  <!-- Deduplicate & Clean -->
  <action>
    <icon>edit-clear</icon>
    <name>Deduplicate &amp; Clean Empty Files</name>
    <unique-id>1779351144290246-3</unique-id>
    <command>/home/v/.local/bin/dedup-clean %F</command>
    <description>Delete all empty files and deduplicate by hash (keeping oldest)</description>
    <patterns>*</patterns>
    <directories/>
  </action>
  
  <!-- Windows Segregation -->
  <action>
    <icon>folder-symbolic</icon>
    <name>Segregate Windows Files</name>
    <unique-id>1779351144290246-4</unique-id>
    <command>python3 /home/v/Projects/Thunar-Action/Windows-Segregation/cli.py --notify %F</command>
    <description>Scan and move Windows-only files and folders to a Windows directory</description>
    <patterns>*</patterns>
    <directories/>
  </action>
  
  <!-- Rsync Placeholder Resolver -->
  <action>
    <icon>system-run</icon>
    <name>Resolve Placeholders (Rsync)</name>
    <unique-id>1779351144290246-5</unique-id>
    <command>python3 /home/v/Projects/Thunar-Action/Placeholder-Rsync-Resolver/cli.py --src %f --notify</command>
    <description>Fetch full-size files for 0-byte placeholders via rsync</description>
    <patterns>*</patterns>
    <directories/>
  </action>
  
  <!-- Paste Dereference Links -->
  <action>
    <icon>edit-paste</icon>
    <name>Paste (Dereference Links)</name>
    <unique-id>1779351144290246-6</unique-id>
    <command>python3 /home/v/Projects/Thunar-Action/Thunar-Paste-Dereference/cli.py %f</command>
    <description>Paste copied files but replace links with their target files/directories</description>
    <patterns>*</patterns>
    <directories/>
  </action>
  
  <!-- Convert to WebP -->
  <action>
    <icon>image-x-generic</icon>
    <name>Convert to WebP</name>
    <unique-id>1779351144290246-7</unique-id>
    <command>python3 /home/v/Projects/Thunar-Action/Thunar-Webp-Optimizer/cli.py %F</command>
    <description>Convert selected images to WebP format</description>
    <patterns>*</patterns>
    <image-files/>
  </action>
  
  <!-- Translate Symlinks -->
  <action>
    <icon>emblem-symbolic-link</icon>
    <name>Translate Symlinks to Relative</name>
    <unique-id>1779351144290246-8</unique-id>
    <command>python3 /home/v/Projects/Thunar-Action/Thunar-Symlink-Translator/cli.py %F</command>
    <description>Convert absolute symbolic links to portable relative ones</description>
    <patterns>*</patterns>
    <directories/>
    <audio-files/>
    <image-files/>
    <other-files/>
    <text-files/>
    <video-files/>
  </action>
  
  <!-- Edit as Root (sudoedit) -->
  <action>
    <icon>accessories-text-editor</icon>
    <name>Edit as Administrator (sudoedit)</name>
    <unique-id>1779351144290246-9</unique-id>
    <command>exo-open --launch TerminalEmulator sudoedit %f</command>
    <description>Edit the selected text file with root privileges using sudoedit</description>
    <patterns>*</patterns>
    <text-files/>
  </action>
</actions>
```


---

## Support & Sponsorship

`Thunar-Action-Collection` is authored and maintained by **[Vikyek](https://github.com/Vikyek)** as an independent open-source project. Everything is 100% open-source, telemetry-free, and public.

<div align="center">


[![Sponsor Vikyek](https://img.shields.io/badge/Sponsor-%E2%9D%A4-ea4aaa?logo=github&style=for-the-badge)](https://github.com/sponsors/Vikyek)
[![Donate on Liberapay](https://img.shields.io/badge/Donate-Liberapay-f6c915?style=for-the-badge&logo=liberapay&logoColor=black)](https://liberapay.com/Vikyek)
[![Donate with Stripe](https://img.shields.io/badge/Donate-Stripe-635BFF?style=for-the-badge&logo=stripe&logoColor=white)](https://profile.stripe.com/@vikyek)

</div>

> ### 🎯 Active Sponsorship Goal: Monthly Living Essentials
> **Target:** **2,710 PLN / ~$680 USD per month** (`630 PLN / week`) — Rent & Essential Utilities  
> Covering basic living essentials directly unlocks dedicated, sustainable full-time independent open-source engineering across Arch Linux utilities, developer tools, and AI middleware free from corporate telemetry, ads, or paywalls.

If this project saves you time, optimizes your setup, or accelerates your workflow, consider supporting ongoing work:

- **GitHub Sponsors**: [github.com/sponsors/Vikyek](https://github.com/sponsors/Vikyek) *(Monthly tiers and one-time tips)*
- **Liberapay**: [liberapay.com/Vikyek](https://liberapay.com/Vikyek) *(0% platform fee recurrent patronage in EUR/USD/PLN)*
- **Direct Stripe Profile**: [profile.stripe.com/@vikyek](https://profile.stripe.com/@vikyek) *(Direct one-time tips & sponsorship)*

Every contribution—monthly or one-time—directly supports active maintenance, hardware testbeds, and new feature development!

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
