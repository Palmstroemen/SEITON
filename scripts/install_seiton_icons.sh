#!/usr/bin/env bash
# The purple SEITON folder icon, for setting it on a folder by hand. The emblems are put in
# place by ./install.sh (installer/seiton_install.py, icons()).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ICONS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons"
FOLDER_SRC="${REPO_ROOT}/assets/icons/seiton-folder-purple.svg"
FOLDER_DEST="${ICONS_DIR}/seiton/seiton-folder-purple.svg"

mkdir -p "$(dirname "${FOLDER_DEST}")"
cp "${FOLDER_SRC}" "${FOLDER_DEST}"

echo "Installed folder icon: ${FOLDER_DEST}"
echo ""
echo "Apply to a folder:"
echo "  gio set -t string <folder> metadata::custom-icon \"file://${FOLDER_DEST}\""
echo "Remove: rm \"${FOLDER_DEST}\""
