#!/usr/bin/env bash
# Upload the site's binary media (MP4, M4A, JPG, PNG, PDF) and the dataset card to the
# Hugging Face dataset repo that the website embeds them from.
#
# The media are kept outside the git repo, in a local mirror of the dataset
# ($FOOD_AI_MEDIA, default /data/media/food-ai; see src/media.py). Paths in the
# mirror and the dataset mirror the site layout, so build_site.py can map a site
# path X to https://huggingface.co/datasets/$REPO/resolve/main/X.
# Re-running is safe: unchanged files are not uploaded again.
#
# Usage: src/publish_assets.sh   (needs `hf auth login` with write access)
# Restore the mirror: hf download nils-holmberg/food-ai --repo-type dataset --local-dir /data/media/food-ai
set -euo pipefail

REPO="nils-holmberg/food-ai"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MEDIA="${FOOD_AI_MEDIA:-/data/media/food-ai}"

hf repos create "$REPO" --type dataset --public --exist-ok
hf upload "$REPO" "$MEDIA" . --type dataset \
  --include "*.mp4" --include "*.m4a" --include "*.jpg" --include "*.png" --include "*.pdf" --exclude ".cache/*" \
  --commit-message "Sync site media"
hf upload "$REPO" "$ROOT/src/hf/README.md" README.md --type dataset \
  --commit-message "Update dataset card"
