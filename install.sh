#!/usr/bin/env bash
# SEITON for this user, from this folder (installer/seiton_install.py does the work).
#
#   ./install.sh                 install, or update after git pull
#   ./install.sh --suntree       also SunTree at login
#   ./install.sh --thumbnailer   also Markdown previews in the file browsers
#   ./install.sh --headline      also the Headline at login (the line at the top edge)
#   ./install.sh --yes           ask nothing
#   ./install.sh --uninstall     take it away again (settings and templates stay)
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is missing: install it with your package manager first." >&2
    exit 1
fi
exec python3 installer/seiton_install.py "$@"
