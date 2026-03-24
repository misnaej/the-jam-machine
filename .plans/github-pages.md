# Plan: GitHub Pages Documentation Site

**Date:** 2026-03-24
**Status:** Planned
**Supersedes:** `notebook-github-pages.md` (absorbed into this broader plan)

---

## Goal

Create a GitHub Pages site for The Jam Machine with:

1. **Landing page** — What is The Jam Machine, how it works at a high level
2. **Encoding/Decoding guide** — How MIDI becomes text tokens, the quantization trade-offs, worked examples
3. **Embedding explorer** — The existing notebook rendered as an interactive page

---

## Site Structure

```
docs/
├── index.html                          # Landing page
├── encoding-decoding.html              # Encoding/decoding guide
├── exploring_the_embedding.html        # Rendered notebook
└── assets/
    ├── encoding_pipeline.png           # Diagram: MIDI → Events → Text → Model
    ├── decoding_pipeline.png           # Diagram: Text → Events → MIDI
    └── piano_roll_example.png          # Example output
```

---

## Page Content

### Page 1: Landing Page (`index.html`)

Brief overview of the project:

- **What it is** — A generative AI music tool that creates MIDI using a GPT-2 model trained on ~5,000 MIDI songs
- **How it works (high level)** — MIDI files are encoded as text tokens → GPT-2 learns to predict next tokens → new music is generated token-by-token → decoded back to MIDI
- **The token vocabulary** — PIECE_START, TRACK_START, INST=, DENSITY=, BAR_START, TIME_DELTA=, NOTE_ON=, NOTE_OFF=, BAR_END, TRACK_END
- **Live demo link** — https://huggingface.co/spaces/JammyMachina/the-jam-machine-app
- **Links to other pages** — encoding/decoding guide, embedding explorer

### Page 2: Encoding/Decoding Guide (`encoding-decoding.html`)

Detailed walkthrough of the encoding and decoding pipeline. This is the educational heart of the site.

**Sections:**

1. **From MIDI to Text**
   - What a MIDI file contains (instruments, notes, timing in ticks)
   - How miditok converts MIDI to Events (Piece-Start, Instrument, Time-Shift, Note-On, etc.)
   - How events become text tokens (the `get_text()` mapping)
   - Example: a short snippet of Reptilia MIDI → the corresponding text tokens

2. **The Token Format**
   - Full vocabulary breakdown with descriptions
   - Example of a complete piece text (abbreviated)
   - How INST=, DENSITY=, TIME_DELTA= values are structured

3. **Quantization and its Trade-offs**
   - Time is quantized to a fixed resolution (currently 4 steps per beat for both drums and non-drums)
   - This means sub-quantization timing (e.g. guitar strums, grace notes, humanized velocity offsets) is lost
   - Zero time deltas are discarded — near-simultaneous notes collapse to the same time step
   - Pitch range: 0–127 (full MIDI range)
   - Instrument familization: 128 MIDI programs are grouped into 16 families for the model's vocabulary

4. **From Text back to MIDI**
   - How text tokens are parsed back to events (`get_event()` mapping)
   - How events are reassembled into a MIDI file (bar structure, time reconstruction)
   - What changes in the roundtrip (timing resolution, instrument programs → families)

5. **Worked Example: The Strokes - Reptilia**
   - Original MIDI stats (instruments, duration, note count)
   - Encoded text preview (first few bars)
   - Decoded MIDI stats (how many instruments, what changed)
   - Piano roll comparison (original vs decoded)
   - This demonstrates the encoding/decoding pipeline and its limitations concretely

### Page 3: Embedding Explorer (`exploring_the_embedding.html`)

The existing notebook, rendered. Contains:
- Attention pattern visualizations (bertviz)
- Token embedding space (TSNE)
- Activation analysis

This page is generated from the notebook (see notebook cleanup steps below).

---

## Implementation Steps

### Step 1: Notebook cleanup (from `notebook-github-pages.md`)

All steps from the previous plan still apply:
- Move `bertviz`, `ipykernel` to `[project.optional-dependencies] notebooks`
- Rename file (remove space)
- Fix hardcoded paths → HuggingFace Hub
- Fix figure output → `output/notebooks/`
- Fix or remove broken cells
- Verify end-to-end execution

### Step 2: Write the encoding/decoding guide

Write as markdown (converted to HTML via a static site tool or simple template).

**Source material:**
- `src/jammy/midi_codec.py` module docstring (quantization caveat)
- `src/jammy/constants.py` (quantization values, instrument families)
- `src/jammy/tokens.py` (full token vocabulary)
- `examples/encode_decode.py` output (Reptilia roundtrip)
- `src/jammy/embedding/encoder.py` and `decoder.py` (pipeline code)

**Include diagrams:**
- Encoding pipeline: `MIDI File → miditok Events → Text Tokens`
- Decoding pipeline: `Text Tokens → Events → MIDI File`
- Can be simple ASCII/mermaid diagrams or created with a tool

### Step 3: Write the landing page

Brief, visual, links to the other pages and the live demo.

### Step 4: Choose a static site tool

Options (in order of preference):

1. **Plain HTML/CSS** — Simplest. Just write HTML files. No build step. Good enough for 3 pages.
2. **Jekyll** — GitHub Pages natively supports it. Write markdown, get HTML. Adds theming for free.
3. **MkDocs / Jupyter Book** — More powerful but more setup. Overkill for 3 pages.

**Recommendation:** Start with Jekyll (GitHub's default). Write pages as markdown in `docs/`, add a `_config.yml` for theme. The notebook is pre-rendered to HTML and linked. Upgrade later if needed.

### Step 5: Set up GitHub Pages

1. Add `docs/` directory with pages
2. Add `docs/_config.yml` for Jekyll (theme, title, etc.)
3. Enable GitHub Pages in repo settings → Source: `docs/` on `main`
4. Link from `README.md`

### Step 6: Build script

```bash
#!/bin/bash
# scripts/build-docs.sh
# Renders the notebook and copies it to docs/
pipenv run jupyter nbconvert --to html \
  notebooks/exploring_the_embedding.ipynb \
  --output-dir docs/
```

The markdown pages are rendered by Jekyll automatically.

---

## Design Decisions

### Why Jekyll over plain HTML?

Jekyll gives us markdown authoring (much easier to maintain than raw HTML), automatic theming, and navigation — all built into GitHub Pages with zero deployment config. The encoding/decoding guide will have a lot of prose and code examples that are painful to write in raw HTML.

### Should the encoding guide include code snippets?

Yes — showing the actual Python (e.g. `get_text()` mappings, quantization logic) makes it concrete. But keep it focused: show the *what* and *why*, not implementation details.

### Should we generate the Reptilia example outputs automatically?

No — pre-generate them once and commit the assets (piano roll PNG, text snippet). The example script already produces these. Avoids needing the full environment to build docs.

---

## Files Changed

| File | Action |
|------|--------|
| `docs/index.md` | **CREATE** — Landing page |
| `docs/encoding-decoding.md` | **CREATE** — Encoding/decoding guide |
| `docs/_config.yml` | **CREATE** — Jekyll config |
| `docs/exploring_the_embedding.html` | **CREATE** — Rendered notebook |
| `docs/assets/` | **CREATE** — Diagrams, example images |
| `notebooks/exploring_the_embedding.ipynb` | **UPDATE** — Fixed notebook |
| `pyproject.toml` | **UPDATE** — notebooks optional group |
| `scripts/build-docs.sh` | **CREATE** — Notebook rendering script |
| `README.md` | **UPDATE** — Link to GitHub Pages |
| `.plans/notebook-github-pages.md` | **DELETE** — Superseded by this plan |

---

## Verification

```bash
# Jekyll serves locally (requires ruby/jekyll installed)
cd docs && bundle exec jekyll serve

# Or just open the markdown files and check rendering on GitHub

# Notebook renders correctly
pipenv run jupyter nbconvert --to html notebooks/exploring_the_embedding.ipynb --output-dir docs/
open docs/exploring_the_embedding.html
```
