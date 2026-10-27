"""Where the archive's files live.

Text (HTML, subtitles, JSON, BibTeX, scripts) is in the git repo under ROOT. Binary media are served from the
Hugging Face dataset HF_DATASET, whose paths mirror ROOT; MEDIA is a local mirror of that dataset (same paths) used by
the build scripts and for uploads. It can be deleted and restored at any time with

    hf download nils-holmberg/food-ai --repo-type dataset --local-dir /data/media/food-ai

FOOD_AI_MEDIA overrides the mirror location.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIA = Path(os.environ.get("FOOD_AI_MEDIA", "/data/media/food-ai"))
MEDIA_SUFFIXES = {".mp4", ".m4a", ".jpg", ".png", ".pdf"}
HF_DATASET = "nils-holmberg/food-ai"


def is_media(rel: str | Path) -> bool:
    return Path(rel).suffix.lower() in MEDIA_SUFFIXES


def local(rel: str | Path) -> Path:
    """Local path of an archive file given its site path, e.g. 'svt/sverige-live.mp4' or 'svt/metadata.json'."""
    return (MEDIA if is_media(rel) else ROOT) / rel
