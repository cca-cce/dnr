---
pretty_name: Food / AI Sourcebook media
license: other
license_name: mixed-third-party
language:
  - en
  - sv
  - de
tags:
  - food
  - generative-ai
  - media-archive
  - uncanny-valley
size_categories:
  - n<1K
---

# Food / AI Sourcebook: media files

Binary media for the **Food / AI Sourcebook**, a research archive on AI-generated food imagery in
restaurant menus and advertising. It was compiled to prepare an SVT Nyheter Helsingborg interview
(October 2026). The website itself (HTML, text, subtitles, metadata, bibliography, build scripts) lives
in the GitHub repository [`cca-cce/dnr`](https://github.com/cca-cce/dnr) under `web/food-ai/`, and
embeds these files directly from this repo.

File paths mirror the website layout, so a site path `X` is served at
`https://huggingface.co/datasets/nils-holmberg/food-ai/resolve/main/X`.

| Path | Content |
|---|---|
| `pdf/food-ai-sourcebook.pdf` | The complete sourcebook as one PDF (text, transcripts, all comments, described images), written for offline reading and retrieval-augmented (RAG) search |
| `pdf/food-ai-intro.pdf`, `pdf/food-ai-<source>.pdf` | The same content split into an introduction and one file per source |
| `references/diel2026ai.pdf` | Diel et al. (2026), *Scientific Reports* 16, 25521, doi:10.1038/s41598-026-66977-1 |
| `instagram/Video_by_jennyfrennberg-DeUPt1mIz5n.mp4` / `.jpg` | The archived Instagram reel by Jenny Frennberg and its thumbnail |
| `guardian/images/`, `cnn/images/`, `reddit/images/` | Images from the archived Guardian and CNN articles and the r/sweden post |
| `svt/nyheter-helsingborg.mp4` / `.jpg` | SVT Nyheter Helsingborg, *Forskaren: Därför väcker AI-bilder på mat ilska* (2026-10-26, 1 min 14 s, 608×1080, H.264/AAC), interview with Nils Holmberg by Joel Sund, and a still |
| `svt/sverige-live.mp4` / `.jpg` | Sverige Live, SVT1, 2026-10-26: the 6 min 30 s segment from Lund (1920×1080, H.264/AAC), and a still |
| `notebook/ai-menu-imagery-infographic.png` / `.jpg` | *AI Menu Imagery: Why Fake Food Is Backfiring on Restaurants*, an infographic generated with Gemini Notebook (2752×1536 PNG, 1600 px JPG preview) |
| `notebook/the-uncanny-menu.pdf`, `notebook/the-uncanny-menu/slide-NN.jpg` | *The Uncanny Menu*, a 15-slide AI-generated deck made with Gemini Notebook (image-only PDF, 1376×768 pt), and each slide as a 1600 px JPG |
| `notebook/why-ai-food-menus-disgust-us.m4a` | *Why AI Food Menus Disgust Us*, an AI-generated audio overview made with Gemini Notebook (25 min 34 s, AAC) |

SHA-256 checksums for every file are listed in `web/food-ai/MANIFEST.sha256` in the GitHub repository.

## Rights and attribution

- `references/diel2026ai.pdf` is © the authors and licensed under
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- The news images (The Guardian, CNN and the photographers credited there), the Instagram reel
  (Jenny Frennberg) and the Reddit photo (u/Sensitive_Cream3920) remain the property of their owners.
  They are archived unchanged for research, criticism and commentary, with sources credited on the website.
  They are **not** licensed for reuse here.
- The SVT clips in `svt/` are © SVT (Sveriges Television). They are archived for research and commentary by the
  interviewee, with the original broadcasts linked on the website, and are **not** licensed for reuse here.
  Subtitles (Swedish, English, German) are served with the website from GitHub.
- The files in `notebook/` are AI-generated with Google's Gemini Notebook and published by the archive's author as
  machine-made summaries; they may contain errors (the website fact-checks the infographic's figures).
- The PDF editions are compilations of the material above, plus editorial descriptions, translations and summaries.

Rights holders who want a file removed can open a discussion on this repository.
