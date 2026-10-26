#!/usr/bin/env bash
# Upload the site's binary media (MP4, JPG, PDF) and the dataset card to the
# Hugging Face dataset repo that the website embeds them from.
#
# Paths in the repo mirror the site layout, so build_site.py can map a local
# path X to https://huggingface.co/datasets/$REPO/resolve/main/X.
# Re-running is safe: unchanged files are not uploaded again.
#
# Usage: src/publish_assets.sh   (needs `hf auth login` with write access)
set -euo pipefail

REPO="nils-holmberg/food-ai"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

hf repos create "$REPO" --type dataset --public --exist-ok
hf upload "$REPO" "$ROOT" . --type dataset \
  --include "*.mp4" --include "*.jpg" --include "*.pdf" --exclude "src/*" \
  --commit-message "Sync site media"
hf upload "$REPO" "$ROOT/src/hf/README.md" README.md --type dataset \
  --commit-message "Update dataset card"
