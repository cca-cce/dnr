# Food + AI materials from `svt.pdf`

The PDF is a three-page Swedish email thread preparing an SVT Nyheter Helsingborg interview about AI-generated food images in restaurant menus and advertising. Its six topical hyperlinks all concern the combined subject of food and AI, so each linked source has its own subdirectory.

## Browse the archive

Open [`index.html`](index.html) for the visual sourcebook. It provides:

- Overview cards and short summaries for all six sources.
- Separate image, video, and text collections.
- Full readable Guardian and CNN article pages.
- Playback of the archived Instagram reel with reviewed English and German subtitles and transcripts.
- A searchable page containing the Reddit post and 198 comments.
- Explicit limitation pages for the blocked New York Times interactive and client-rendered TikTok discovery feed.

The static site has no external software dependencies. Pages, text and subtitles use relative links; binary media load from the Hugging Face dataset described under “Media hosting” (or from the local copies when built with `FOOD_AI_LOCAL_ASSETS=1`).

## Link archive

| Subdirectory | Source | Saved material | Status |
|---|---|---|---|
| `nytimes/` | New York Times, “Why A.I. Food Slop Looks So Gross” | Direct HTML response and metadata | Publisher anti-bot page; article could not be retrieved, including via the public gift link |
| `guardian/` | The Guardian | Raw HTML, readable article text, metadata, article images | Complete |
| `cnn/` | CNN | Raw HTML, readable article text, metadata, article images | Complete |
| `instagram/` | Instagram reel by Jenny Frennberg | Raw HTML, merged MP4, thumbnail, yt-dlp metadata, readable description | Complete |
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

- `pdf/` (hosted on Hugging Face, see “Media hosting”) holds the complete sourcebook (`food-ai-sourcebook.pdf`) and one PDF per section (`food-ai-intro.pdf`, `food-ai-<source>.pdf`), written for offline reading and retrieval-augmented (RAG) search. They are linked from the “PDF editions” section of `index.html`.
- `references/food-ai.bib` is a BibTeX bibliography of the research literature, the six archived sources, and the reporting and industry sources they cite (keys follow the Google Scholar pattern). Open-access full text is stored as `references/<key>.pdf` where the license allows (currently `diel2026ai.pdf`, CC BY 4.0). `pages/references.html` renders the bibliography.

## Scripts

All build scripts live in `src/` and locate the archive from their own path, so run them from anywhere (shown here from the archive root, using the project's Python environment):

| Script | Purpose |
|---|---|
| `src/process_materials.py` | Re-downloads and processes the linked sources into the per-source directories, then writes `MANIFEST.sha256`. `--manifest-only` refreshes only the checksums. |
| `src/build_site.py` | Regenerates `index.html` and `pages/*.html` (including the references page built from `references/food-ai.bib`). Standard library only. |
| `src/build_book.py` | Builds the PDF editions in `pdf/` (optional output directory argument). Needs PyMuPDF, Pillow, ffmpeg, and headless Chromium. |
| `src/page_metadata.py` | Prints title, author, and date metadata from saved HTML pages; used when compiling the bibliography. |
| `src/publish_assets.sh` | Uploads the binary media (`*.mp4`, `*.jpg`, `*.pdf`) and the dataset card `src/hf/README.md` to the Hugging Face dataset repo. Unchanged files are skipped. |

Typical rebuild after changing content:

    python src/build_book.py && src/publish_assets.sh && python src/build_site.py && python -B src/process_materials.py --manifest-only

## Media hosting

Binary media (the Instagram MP4, all JPG images, and the PDFs in `pdf/` and `references/`) are served from the Hugging Face dataset [`nils-holmberg/food-ai`](https://huggingface.co/datasets/nils-holmberg/food-ai), whose paths mirror this directory. `src/build_site.py` writes `https://huggingface.co/datasets/nils-holmberg/food-ai/resolve/main/<path>` for them. The files stay on disk for the build scripts and `MANIFEST.sha256`, but are git-ignored (`.gitignore`). Subtitles, text, JSON, the bibliography and raw HTML responses stay in git and are served alongside the pages.

For an offline preview that links the local copies instead, build with `FOOD_AI_LOCAL_ASSETS=1 python src/build_site.py`, then rebuild without the variable before committing.
