---
name: demo-video
description: Make a short landscape demo or promo video of a code library or tool, for X, LinkedIn or a README, entirely from code. Real output captured from the released package in a Python REPL, scenes drawn in HTML and rendered frame by frame in headless Chromium, H.264 through ffmpeg, an optional original synthesized music bed, and optional edge-tts narration (en-US-GuyNeural, rate +5%). Use for a promo, demo, launch or README video of a project (宣传视频, 演示视频). Not for AI-generated footage, recordings of a person, or slide decks.
---

# Demo Video

A one-minute video that shows a library doing real work: a title, the README's overview figure revealed in steps, three or four terminal scenes that replay real REPL output and ring the lines that matter, a real screenshot of a viewer, and an end card with the install command. Scripts in this skill generate every frame and every sound, so changing a caption, a scene or the music means a re-render of a few minutes.

## When to Use

- A project is about to be promoted and needs a video for X, LinkedIn or the top of its README.
- The project has a Python API whose output can be shown in a terminal, and a README figure or screenshot worth animating.

## When Not to Use

- Footage of people, AI-generated video, or anything that needs a camera. This skill only draws.
- A slide deck or a single static figure: use a presentation workflow, `readme-polish`, `ci-mockup-figure`, or `figure-prompt-builder`.

## Rules

1. **Real output only.** Every terminal line comes from `capture_repl.py` running the code shown on screen against the released package, installed from the package index at the version the video names. Never write or edit output by hand; when output is too long, change the code the video shows (for example a `max_chars=` argument) and capture again. Only the timing of typing and printing is compressed. A screenshot must be a real capture, and the record says which screenshots were reused.
2. **Every caption is checkable.** Counts, supported tools and versions in titles and callouts must match the project's README or documentation.
3. **The video works silent.** X and LinkedIn autoplay muted and a README video plays muted, so titles and callouts carry the story; music and narration are additions.
4. **Ask where it will be posted** before building, since that decides aspect ratio and length. Default: 16:9, 1920x1080, 30 fps, about 60 s.
5. **The agent cannot hear audio.** Check music and narration by the printed level, line lengths and gaps, say that this is all that was checked, and ask the user to listen before committing.
6. **Show stills before the full render**, then a contact sheet and the opened file after it.

## Storyboard

| Scene | Length | Content |
|---|---|---|
| Title | 4–5 s | Logo and the README tagline |
| Overview | 10–12 s | The README overview figure, revealed region by region, with one caption per region |
| Terminal × 3–4 | about 10 s each | Kicker (the API call), a title of at most six words, a one-line subtitle; real REPL output; one ring with one callout, or up to three callouts |
| Viewer | 5 s | A real screenshot of the output in a viewer, slowly zooming |
| End card | 5 s | Logo, install command, repository address, licence and version |

A terminal at 120 columns and 20 px holds 26 lines and scrolls beyond that. A short output can use a larger font (`fs`) and a window fitted to it (`fit`). Callouts on adjacent lines overlap, so keep them at least 1.5 lines apart (`dy`). Ring whole rows when a callout names a column such as a step number; a zoom that crops that column defeats the callout.

## Pipeline

Environments: a capture environment with the released package, the extras the scenes use, rich and pygments (`pip install "pkg[extras]==X.Y.Z" rich pygments`), and a render environment with playwright and its Chromium, imageio-ffmpeg (it bundles an ffmpeg built with libx264), numpy, scipy, and edge-tts when narrating.

1. **Capture.** Write `SCENES.json`, mapping each terminal scene's name to the lines typed at the prompt (an empty line closes an indented block). Run `python scripts/capture_repl.py SCENES.json SITE/data.js` in the capture environment. It prints the transcript and each scene's line count; change the code, never the output, until each scene fits.
2. **Site.** Copy `assets/template.html` to `SITE/index.html` and `assets/video.example.js` to `SITE/video.js`, put the logo, overview figure and screenshots in `SITE`, and edit `video.js` (scene types below; the example is a complete 63 s video).
3. **Stills.** `python scripts/render.py SITE --timeline timeline.json` prints each scene's start and length (a terminal scene's length depends on its output). Then `python scripts/render.py SITE STILLS --stills 2.5,9,24,...` at the moments each ring and callout is complete, about one second before a terminal scene ends, and look at every still before going on.
4. **Render.** `python scripts/render.py SITE --video picture.mp4` screenshots every frame and pipes it to libx264 (CRF 18, yuv420p, faststart). About three minutes for 60 s.
5. **Music** (when wanted). `python scripts/music.py music.wav --duration D --groove START END`, with START the first terminal scene's start and END the end card's start, from `timeline.json`. The track is synthesized from sine partials and filtered noise, so it carries no licence.
6. **Narration** (only when asked). Write `NARRATION.json` as lines by scene and offset (`assets/narration.example.json`), then `python scripts/narrate.py NARRATION.json voice.wav --timeline timeline.json`. It prints each line's length and the gap to the next, and stops when a line runs into the next one.
7. **Mix.** `python scripts/mix.py picture.mp4 OUT.mp4 --music music.wav --voice voice.wav` (either flag alone works) ducks the music 9 dB under the voice and muxes AAC without re-encoding the picture. A silent video is `picture.mp4` itself.
8. **Verify and record.** Check duration and streams, build a contact sheet of eight to ten frames, open the file for the user, and save the video with its sources and a short note on how it was made in the project's records.

## Scene Types

Every scene takes `type` and `name` (the timeline and the narration refer to scenes by name), and every scene except `terminal` takes `dur`; a terminal scene lasts as long as its typing and output, plus `hold`.

| `type` | Fields |
|---|---|
| `title` | `logo`, `tagline`, `logoWidth`, `logoTop` |
| `figure` | `src`, `width`, `top`, `reveal` (`[{x0, x1, at, dur}]` in fractions of the width), `captions` (`[{at, until, html}]`), `zoom` |
| `terminal` | `name` (its key in `data.js`), `kicker`, `title`, `subtitle`, `hold`, `fs`, `fit`, `paste` (the first N lines appear at once, as a paste), `cps`, `focus` (`{from, to, extra, col0, col1, zoom}`), `notes` (`[{at, dy, col, text}]`); `from`, `to` and `at` are regular expressions matched against the display lines |
| `image` | `src`, `frame` (`browser` or `plain`), `address`, `width`, `height`, `zoom`, plus the header fields |
| `end` | `logo`, `command`, `url`, `fine` |
| `custom` | `build`, `ready` and `render` functions in `VIDEO.custom[name]`, for example to animate an HTML figure's own elements in a same-origin iframe |

`renderFrame(t)` must set every animated property from `t` alone: no CSS transitions, timers or state carried from the previous frame, or a re-render will not reproduce a frame. `VIDEO.theme` sets the page's CSS variables; the colors of captured output come from `THEME` and `CODE_COLORS` in `capture_repl.py`.

## Platforms

- **X.** H.264 High, yuv420p, AAC, 16:9. Standard accounts post up to 2 min 20 s.
- **README on GitHub.** A video plays only from an uploaded attachment: drag the mp4 into an issue or pull request comment box and put the resulting `user-attachments` URL on its own line. A path inside the repository renders as a link. For an inline loop, cut 8–15 s to a GIF at 960 px with an ffmpeg palette.
- **Phones.** 20 px terminal text is small at phone size; the 58 px titles, the callouts and the zoom carry the scene there.

## Narration

The default is edge-tts with `en-US-GuyNeural` at rate `+5%`, the maintainer's choice; it speaks about three words per second, so a 10 s scene holds 20 to 25 words with room before the next. Spell names as they should sound ("agent pile", "Who and When"). edge-tts is an unofficial client of the online read-aloud service in Microsoft Edge: it needs the network, sends the text to Microsoft, and can stop working without notice. Azure AI Speech sells the same voices under a licence. The user's own recorded voice beats any synthesized one when they are willing to record it.

## Lessons From the First Video

- Playwright's `recordVideo` gives a soft WebM that drops frames; deterministic frames with one screenshot each do not. `render.py` serves the site over HTTP so an iframe figure shares the page's origin.
- ffmpeg's `-shortest` dropped the last four frames when muxing, and the container still reported the full length; count frames, not seconds.
- Chromium drops a very large `box-shadow` spread inside a scaled layer, so a spotlight built that way vanished when the camera zoomed; the template dims with four masks.
- An SVG path drawn with `stroke-dasharray` and a round cap shows a dot before it starts drawing; keep it hidden until it has progress.
- rich prints colors to a redirected stream only when `FORCE_COLOR`, `COLORTERM`, `TERM` and `COLUMNS` are set; with an agent shell's `TERM=dumb` it drops colors and wraps at 80 columns. The REPL echoes an expression's value even inside a `with` block. Capture what prints; do not predict it.
- A contact sheet can hide a real effect: a dim that looked absent in thumbnails measured at half brightness. Measure pixels before changing something that works.
- The synthesized music was checked by level curve, spectrogram, peak and largest sample step (a click is above 0.3), and then by the user's ear.

## Files

- `scripts/capture_repl.py`: run scene lines in a real REPL and write `data.js`.
- `scripts/render.py`: stills, the timeline, and the H.264 render.
- `scripts/music.py`: the original background track.
- `scripts/narrate.py`: edge-tts narration placed on the timeline.
- `scripts/mix.py`: duck, mix and mux.
- `assets/template.html`: the scene engine; `assets/video.example.js`, `assets/scenes.example.json` and `assets/narration.example.json`: the agentpile 0.3.1 video as a worked example.
