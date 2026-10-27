# Food + AI materials from `svt.pdf`

The PDF is a three-page Swedish email thread preparing an SVT Nyheter Helsingborg interview about AI-generated food images in restaurant menus and advertising. Its six topical hyperlinks all concern the combined subject of food and AI, so each linked source has its own subdirectory.

## Browse the archive

Open [`index.html`](index.html) for the visual sourcebook. It provides:

- The resulting SVT interviews with Joel Sund (SVT Nyheter Helsingborg and Sverige Live, 26 October 2026) on `pages/svt.html`, with English, Swedish and German subtitles and clickable, searchable transcripts. SVT Nyheter's 52-second Instagram reel of the story is on `pages/videos.html`, next to Jenny Frennberg's reel, with a static selection of viewers' comments and a link to the full discussion on Instagram.
- An AI-generated infographic and a 25½-minute audio overview (Gemini Notebook) on `pages/notebook.html`, with a fact-check of the infographic's figures and a clickable, searchable transcript; and the 15-slide AI-generated deck *The Uncanny Menu* on `pages/slides.html`, with each slide's text written out.
- Overview cards and short summaries for all six sources.
- Separate image, video, and text collections.
- Full readable Guardian and CNN article pages.
- Playback of the archived Instagram reel with reviewed English and German subtitles and transcripts.
- A searchable page containing the Reddit post and 198 comments.
- Explicit limitation pages for the blocked New York Times interactive and client-rendered TikTok discovery feed.

The static site has no external software dependencies. Pages, text and subtitles use relative links; binary media load from the Hugging Face dataset described under “Media hosting” (or from the local mirror when built with `FOOD_AI_LOCAL_ASSETS=1`).

## Link archive

| Subdirectory | Source | Saved material | Status |
|---|---|---|---|
| `nytimes/` | New York Times, “Why A.I. Food Slop Looks So Gross” | Direct HTML response and metadata | Publisher anti-bot page; article could not be retrieved, including via the public gift link |
| `guardian/` | The Guardian | Raw HTML, readable article text, metadata, article images | Complete |
| `cnn/` | CNN | Raw HTML, readable article text, metadata, article images | Complete |
| `instagram/` | Instagram reel by Jenny Frennberg | Raw HTML, merged MP4, thumbnail, yt-dlp metadata, readable description | Complete |
| `notebook/` | AI-generated summaries made with Gemini Notebook (not one of the six links) | Infographic PNG with JPG preview, M4A audio overview, slide-deck PDF (`the-uncanny-menu.pdf`, image-only) with one JPG per slide, English WebVTT and `.txt` transcript, metadata, `content.txt` | Complete; transcript by Whisper small with names corrected against the archive, otherwise not proofread |
| `svt/` | The SVT interviews themselves (not one of the six links) | Two MP4 clips plus SVT Nyheter's Instagram reel (`svtnyheter-instagram`, Swedish subtitles burned in) with stills, WebVTT subtitles and `.txt` transcripts (`<clip>.<sv/en/de>.*`), metadata (including the reel's caption and comment highlights), Swedish transcripts in `content.txt` | Complete; Swedish transcribed with KBLab/kb-whisper-large and proofread, English and German translated with the same timings |
| `tiktok/` | TikTok discovery page | Raw HTML and metadata | Page archived; discovery results require client-side/API loading and were not exposed in the response |
| `reddit/` | r/sweden discussion | Raw page responses, Atom thread with the post and 198 comments, readable text, original attached image, metadata | Complete via Atom feed |

Each directory contains `metadata.json` and `content.txt`. `source.html` is the unmodified direct response. `MANIFEST.sha256` records checksums for verification.

## PDF analysis

The interview request frames the phenomenon as a move from online generative imagery into ordinary physical communication: menus, food trucks, signs, and restaurant advertising. It asks why adoption is happening, why reactions are unusually intense for food, why the images have a recognizable visual character, whether “uncanny valley” is a useful explanation, and whether audiences will habituate as synthetic imagery becomes more common.

The linked material supplies three complementary evidence types:

- News reporting and expert interpretation from the New York Times, Guardian, and CNN.
- Concrete visual examples and criticism on Instagram and TikTok.
- A Swedish audience discussion on Reddit, useful for local reactions and language.

Across the accessible sources, recurring explanations include low production cost and speed for businesses; visual defects in texture, anatomy, repetition, and food structure; learned expectations that food imagery should represent something actually available; disgust/contamination cues; and distrust created when a synthetic image substitutes for evidence of the real dish. “Uncanny valley” is relevant as shorthand for near-real but perceptually wrong imagery, though food-specific disgust and truth-in-advertising expectations add mechanisms beyond the term’s original human/robot context.

## PDF editions and bibliography

- `pdf/` (hosted on Hugging Face and kept in the media mirror, see “Media hosting”) holds the complete sourcebook (`food-ai-sourcebook.pdf`) and one PDF per section (`food-ai-intro.pdf`, `food-ai-<source>.pdf`), written for offline reading and retrieval-augmented (RAG) search. They are linked from the “PDF editions” section of `index.html`.
- `references/food-ai.bib` is a BibTeX bibliography of the research literature, the six archived sources, and the reporting and industry sources they cite (keys follow the Google Scholar pattern). Open-access full text is stored as `references/<key>.pdf` where the license allows (currently `diel2026ai.pdf`, CC BY 4.0). `pages/references.html` renders the bibliography.

## Scripts

All build scripts live in `src/` and locate the archive from their own path, so run them from anywhere (shown here from the archive root, using the project's Python environment):

| Script | Purpose |
|---|---|
| `src/process_materials.py` | Re-downloads and processes the linked sources into the per-source directories (images into the media mirror), then writes `MANIFEST.sha256`. `--manifest-only` refreshes only the checksums. |
| `src/build_site.py` | Regenerates `index.html` and `pages/*.html` (including the references page built from `references/food-ai.bib`). Standard library only. |
| `src/build_book.py` | Builds the PDF editions in the mirror's `pdf/` (optional output directory argument). Needs PyMuPDF, Pillow, ffmpeg, and headless Chromium. |
| `src/page_metadata.py` | Prints title, author, and date metadata from saved HTML pages; used when compiling the bibliography. |
| `src/media.py` | Where files live: text under this directory, binary media in the mirror (`FOOD_AI_MEDIA`, default `/data/media/food-ai`). Imported by the other scripts. |
| `src/publish_assets.sh` | Uploads the binary media (`*.mp4`, `*.jpg`, `*.pdf`) from the mirror and the dataset card `src/hf/README.md` to the Hugging Face dataset repo. Unchanged files are skipped. |

Typical rebuild after changing content:

    python src/build_book.py && src/publish_assets.sh && python src/build_site.py && python -B src/process_materials.py --manifest-only

## Media hosting

Binary media (the Instagram and SVT MP4s, the M4A audio overview, all JPG and PNG images, and the PDFs in `pdf/` and `references/`) are served from the Hugging Face dataset [`nils-holmberg/food-ai`](https://huggingface.co/datasets/nils-holmberg/food-ai), whose paths mirror this directory. `src/build_site.py` writes `https://huggingface.co/datasets/nils-holmberg/food-ai/resolve/main/<path>` for them. They are not in this directory: the local copies live in a mirror of the dataset with the same paths, `/data/media/food-ai` (override with `FOOD_AI_MEDIA`), used by the build scripts, `MANIFEST.sha256` and uploads. Restore or refresh it with

    hf download nils-holmberg/food-ai --repo-type dataset --local-dir /data/media/food-ai

`.gitignore` still excludes `*.mp4`, `*.jpg` and `*.pdf` as a safety net. Subtitles, text, JSON, the bibliography and raw HTML responses stay in git and are served alongside the pages. New media go into the mirror (same path as the page would use), then `src/publish_assets.sh`.

For an offline preview that links local copies instead, build with `FOOD_AI_LOCAL_ASSETS=1 python src/build_site.py` and serve the repo with a server that falls back to the mirror and supports Range requests (video seeking), e.g. `python3 ~/rnd/d/specs/skill-hf-av/scripts/rangeserver.py ~/rnd/d/html/dnr 8766 --overlay web/food-ai=/data/media/food-ai`, then open http://127.0.0.1:8766/web/food-ai/. Rebuild without the variable before committing.
