# Food + AI materials from `svt.pdf`

The PDF is a three-page Swedish email thread preparing an SVT Nyheter Helsingborg interview about AI-generated food images in restaurant menus and advertising. Its six topical hyperlinks all concern the combined subject of food and AI, so each linked source has its own subdirectory.

## Browse the archive

Open [`index.html`](index.html) for the visual sourcebook. It provides:

- Overview cards and short summaries for all six sources.
- Separate image, video, and text collections.
- Full readable Guardian and CNN article pages.
- Local playback of the archived Instagram reel with reviewed English subtitles and transcript.
- A searchable page containing the Reddit post and 198 comments.
- Explicit limitation pages for the blocked New York Times interactive and client-rendered TikTok discovery feed.

The static site has no external software dependencies and uses relative links, so it can be served locally or copied with the archive as one directory.

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
