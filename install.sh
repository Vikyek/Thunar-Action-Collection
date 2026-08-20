#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"

echo "=== Installing Thunar-Action-Collection ==="

# Check requirements
for cmd in python3 rsync notify-send; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Warning: '$cmd' is not installed."
    fi
done

# Initialize submodules if cloned with git
if [ -d "${SCRIPT_DIR}/.git" ]; then
    git -C "${SCRIPT_DIR}" submodule update --init --recursive || true
fi

mkdir -p "${BIN_DIR}"

# Run install scripts of submodules if present
for sub in dedup-clean Placeholder-Rsync-Resolver Thunar-Paste-Dereference Thunar-Symlink-Translator Thunar-Webp-Optimizer Windows-Segregation; do
    if [ -f "${SCRIPT_DIR}/${sub}/install.sh" ]; then
        echo "Installing submodule: ${sub}..."
        bash "${SCRIPT_DIR}/${sub}/install.sh" || echo "Warning: ${sub} install script encountered an error."
    fi
done

echo "Thunar Action Collection installation complete!"
echo "Refer to README.md for uca.xml Thunar custom action registration."
