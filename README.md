# Thunar Custom Actions Collection

This repository acts as a central index and grouping for custom Thunar action scripts and utilities designed to enhance the Thunar File Manager on Linux.

## Collection Overview

The collection consists of the following tools:

### 1. [Thunar-Paste-Dereference](https://github.com/Vikyek/Thunar-Paste-Dereference)
*   **Description:** Pastes copied files/folders from clipboard but dereferences symbolic links, copying the actual targets. Supports both Wayland (`wl-paste`) and X11 (`xclip`).
*   **Thunar Command:** `python3 /home/v/Projects/Thunar-Action/Thunar-Paste-Dereference/cli.py %f`

### 2. [Windows-Segregation](https://github.com/Vikyek/Windows-Segregation)
*   **Description:** Scans and moves Windows-only system files or directories to a dedicated Windows folder to clean up Linux workspaces.
*   **Thunar Command:** `python3 /home/v/Projects/Thunar-Action/Windows-Segregation/cli.py --notify %F`

### 3. [Placeholder-Rsync-Resolver](https://github.com/Vikyek/Placeholder-Rsync-Resolver)
*   **Description:** Resolves 0-byte placeholder files by downloading their actual content from a remote server using Rsync.
*   **Thunar Command:** `python3 /home/v/Projects/Thunar-Action/Placeholder-Rsync-Resolver/cli.py --src %f --notify`

### 4. [dedup-clean](https://github.com/Vikyek/dedup-clean)
*   **Description:** Deduplicates files by hash (keeping the oldest version) and cleans up empty files.
*   **Thunar Command:** `/home/v/.local/bin/dedup-clean %F`

### 5. [Thunar-Webp-Optimizer](https://github.com/Vikyek/Thunar-Webp-Optimizer)
*   **Description:** Converts selected images to the modern WebP format, supporting compression control.
*   **Thunar Command:** `python3 /home/v/Projects/Thunar-Action/Thunar-Webp-Optimizer/cli.py %F`

### 6. [Thunar-Symlink-Translator](https://github.com/Vikyek/Thunar-Symlink-Translator)
*   **Description:** Translates absolute symlinks in selected folders/files to relative ones to keep them portable across machines.
*   **Thunar Command:** `python3 /home/v/Projects/Thunar-Action/Thunar-Symlink-Translator/cli.py %F`

### 7. Edit as Administrator (sudoedit)
*   **Description:** Securely edits text files with root privileges using your default `$EDITOR` via standard `sudoedit`.
*   **Thunar Command:** `exo-open --launch TerminalEmulator sudoedit %f`

## uca.xml Configuration reference

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
