# Plan: Notebook Cleanup & GitHub Pages

**Date:** 2026-03-24
**Status:** Planned

---

## Goal

Make `notebooks/exploring_the_embedding.ipynb` re-runnable by anyone, then publish it as a GitHub Page. The notebook explores the GPT-2 model's learned token embeddings and attention patterns — valuable for understanding how the model represents MIDI tokens.

---

## Current State

| Item | Status |
|------|--------|
| Notebook location | `notebooks/exploring_the _embedding.ipynb` (note: space in filename) |
| Hardcoded paths | `/Users/jean/WORK/DSR_2022_b32/...` — broken for everyone else |
| Dependencies | `bertviz`, `ipykernel` are in main `dependencies` (should be optional) |
| Broken cells | "Untrained Model (NOT WORKING)" attention cell, "WORK IN PROGRESS" at bottom |
| Figure output | Saves to `./figures/` and repo root — no output dir management |
| Package usage | Does its own tokenization — doesn't use `jammy` package at all |
| Filename | Has a space — causes issues with some tools |

---

## Steps

### Step 1: Move notebook deps to optional group in `pyproject.toml`

Move `bertviz`, `ipykernel`, and `scikit-learn` (needed for TSNE) out of main `dependencies` into a new optional group:

```toml
[project.optional-dependencies]
ci = ["ruff", "pytest", "pytest-cov", "pytest-html", "pip-audit"]
notebooks = ["bertviz", "ipykernel", "scikit-learn"]
```

Remove `bertviz` and `ipykernel` from main `dependencies`. `scikit-learn` may already be pulled transitively but should be explicit for the notebooks.

Installation becomes:
```bash
pipenv install -e ".[notebooks]"
```

### Step 2: Fix the notebook

**Rename file:** `exploring_the _embedding.ipynb` → `exploring_the_embedding.ipynb` (remove space)

**Add setup cell at top** (markdown + code):
```markdown
## Setup

To run this notebook, install the notebook dependencies:

```bash
pipenv install -e ".[notebooks]"
```

Then launch Jupyter:

```bash
pipenv run jupyter notebook notebooks/exploring_the_embedding.ipynb
```
```

**Fix data/model loading (cell 12):**
- Replace hardcoded local paths with HuggingFace Hub loading
- Dataset: `load_dataset("JammyMachina/elec-gmusic-familized", ...)`
- Model: `GPT2LMHeadModel.from_pretrained("JammyMachina/elec-gmusic-familized-model-13-12__17-35-53", output_attentions=True)`
- Tokenizer: Load from the model repo (it should have tokenizer.json)

**Fix figure output:**
- Create `output/notebooks/` directory (gitignored)
- Update all `savefig()` calls to use that directory
- Update `figure_path` variable

**Fix or remove broken cells:**
- Debug the untrained model attention cell if feasible, otherwise mark clearly as "Known issue" with explanation
- Clean up or remove the "WORK IN PROGRESS" past key values section — or keep with a clear "experimental" label

**Clean up cells:**
- Remove empty cells
- Add clear section descriptions
- Ensure all cells run top-to-bottom without error

### Step 3: Verify notebook runs end-to-end

```bash
pipenv install -e ".[notebooks]"
pipenv run jupyter nbconvert --to notebook --execute notebooks/exploring_the_embedding.ipynb --output executed_notebook.ipynb
```

This will execute all cells and fail if any cell errors. The executed notebook with outputs can be used for the GitHub Page.

### Step 4: Set up GitHub Pages

**Approach:** Use `nbconvert` to render the notebook to HTML, commit to `docs/`, enable GitHub Pages.

1. Add a script `scripts/build-docs.sh`:
   ```bash
   #!/bin/bash
   pipenv run jupyter nbconvert --to html \
     --no-input \
     notebooks/exploring_the_embedding.ipynb \
     --output-dir docs/
   ```
   (`--no-input` hides code cells for a cleaner page — optional, discuss with user)

2. Create `docs/index.html` that either:
   - Is the rendered notebook directly, or
   - Is a landing page that links to the rendered notebook

3. Enable GitHub Pages in repo settings → Source: `docs/` folder on `main` branch

4. Link from `README.md`:
   ```markdown
   **[Explore the Model's Embedding →](https://misnaej.github.io/the-jam-machine/exploring_the_embedding.html)**
   ```

### Step 5: Optional — GitHub Action for auto-rendering

If we want the page to auto-update when the notebook changes:

```yaml
# .github/workflows/docs.yml
name: Build docs
on:
  push:
    paths: ['notebooks/**']
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install pipenv && pipenv install -e ".[notebooks]"
      - run: pipenv run jupyter nbconvert --to html notebooks/exploring_the_embedding.ipynb --output-dir docs/
      - uses: peaceiris/actions-gh-pages@v3
        with: { github_token: '${{ secrets.GITHUB_TOKEN }}', publish_dir: ./docs }
```

This is optional — manual rendering and committing to `docs/` works fine for a notebook that doesn't change often.

---

## Design Decisions

### Why not use Jupyter Book / Quarto?

Overkill for a single notebook. Plain `nbconvert` to HTML is simple, has no extra dependencies, and produces a good-looking page. Can upgrade later if we add more notebooks.

### Code cells visible or hidden on the page?

Default to **visible** — this is an educational notebook where the code is part of the content. The user can decide during implementation.

### Should the notebook use `jammy` package imports?

The notebook's tokenization code is independent of the `jammy` package — it loads directly from HuggingFace and uses `transformers` APIs. This is actually fine because the notebook is about exploring the **model** not the encoding pipeline. Keeping it self-contained makes it easier to run in isolation (e.g., in Colab). Don't refactor to use `jammy` imports.

---

## Files Changed

| File | Action |
|------|--------|
| `notebooks/exploring_the _embedding.ipynb` | **DELETE** (space in name) |
| `notebooks/exploring_the_embedding.ipynb` | **CREATE** (fixed version) |
| `pyproject.toml` | **UPDATE** move bertviz/ipykernel to optional notebooks group |
| `docs/exploring_the_embedding.html` | **CREATE** rendered notebook |
| `docs/index.html` | **CREATE** (optional landing page) |
| `scripts/build-docs.sh` | **CREATE** rendering script |
| `README.md` | **UPDATE** link to GitHub Page |
| `.gitignore` | **UPDATE** add `output/notebooks/` |

---

## Verification

```bash
# Notebook dependencies install cleanly
pipenv install -e ".[notebooks]"

# Notebook executes without errors
pipenv run jupyter nbconvert --to notebook --execute notebooks/exploring_the_embedding.ipynb

# HTML renders correctly
pipenv run jupyter nbconvert --to html notebooks/exploring_the_embedding.ipynb --output-dir docs/
open docs/exploring_the_embedding.html

# Main app still works without notebook deps
pipenv install -e "."  # no [notebooks]
pipenv run python app/playground.py
```
