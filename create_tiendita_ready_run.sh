#!/usr/bin/env bash
set -euo pipefail

# create_tiendita_ready_run.sh
# Creates a ready-to-run ZIP of the repository contents (excluding .git and workflow artifacts).
# Usage:
#   chmod +x create_tiendita_ready_run.sh
#   ./create_tiendita_ready_run.sh

OUT="tiendita-ready.zip"
EXCLUDES=(".git/*" ".github/workflows/*" "*.pyc" "__pycache__/*")

echo "Removing previous $OUT if present..."
rm -f "$OUT"

echo "Creating zip archive $OUT (excluding: ${EXCLUDES[*]})"
zip -r "$OUT" . ${EXCLUDES[@]/#/-x }

echo "Archive created:"
ls -lh "$OUT"