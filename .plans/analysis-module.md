# Plan: Analysis Module + Notebook Refactor

**Date:** 2026-03-27
**Status:** Planned

---

## Goal

Extract notebook visualizations into a proper `jammy.analysis` Python module. Make them testable, reusable, and improved. Then rebuild the notebook as a thin orchestrator that imports from this module.

The visualizations are educational — they help understand how the GPT-2 model represents and generates MIDI music internally.

---

## Module Structure

```
src/jammy/analysis/
├── __init__.py
├── embedding.py      # Token embedding visualizations
├── attention.py      # Attention pattern analysis
├── activation.py     # Next-token prediction plots
└── head_roles.py     # Attention head specialization analysis
```

---

## PR 1: Embedding visualizations (`embedding.py`)

### Functions

**`plot_embedding_heatmap(model, tokenizer) → Figure`**
- Extract the 301×512 embedding matrix
- Group tokens by category (structure, instruments, notes, time, special)
- Show as heatmap with clear separators and category labels on y-axis
- Improvement over notebook: readable y-axis labels, grouped by category

**`plot_tsne(model, tokenizer) → Figure`**
- TSNE dimensionality reduction (512 → 2)
- Color by token category
- Clean legend: "Notes", "Instruments", "Time", "Structure" instead of "05_NOTE"
- Larger dots, better spacing
- Optional: plotly version with hover labels showing actual token names

**`plot_embedding_comparison(trained_model, untrained_model, tokenizer) → Figure`**
- Side-by-side TSNE: trained vs untrained
- Same random seed so positions are comparable
- Shows at a glance how training organizes the embedding space

### Tests

- `test_plot_embedding_heatmap` — returns a Figure, no NaN in data
- `test_plot_tsne` — returns a Figure, correct number of points
- `test_plot_embedding_comparison` — returns a Figure with 2 subplots

---

## PR 2: Activation visualizations (`activation.py`)

### Functions

**`plot_top_predictions(model, tokenizer, sequence, top_k=10) → Figure`**
- For each token position, show a horizontal bar chart of top-K predicted next tokens
- Each subplot: one position in the sequence
- Bar labels = token names, bar length = probability
- Much more readable than the current full-vocab curve

**`plot_prediction_comparison(trained_model, untrained_model, tokenizer, sequence) → Figure`**
- Side-by-side: trained vs untrained predictions for the same sequence
- Shows how training makes predictions sharp and musically coherent

### Tests

- `test_plot_top_predictions` — returns Figure, correct subplot count
- `test_plot_prediction_comparison` — returns Figure with 2 columns

---

## PR 3: Attention visualizations (`attention.py`)

### Functions

**`plot_attention_heatmap(model, tokenizer, sequence, layer=None) → Figure`**
- seq_len × seq_len heatmap showing attention weights
- If layer=None, show all layers as subplots
- Token names as axis labels
- Reveals patterns: NOTE_OFF → NOTE_ON, BAR_START → previous BAR_END

**`plot_layer_flow(model, tokenizer, sequence, target_position=-1) → Figure`**
- For a single target token, show which tokens it attends to at each layer
- Stacked bar charts: one row per layer, bars = attention weights on source tokens
- Shows how information builds up: early layers = local context, later layers = global structure

### Tests

- `test_plot_attention_heatmap` — returns Figure, correct dimensions
- `test_plot_layer_flow` — returns Figure, correct number of layers

---

## PR 4: Head specialization (`head_roles.py`) — stretch goal

### Functions

**`analyze_head_roles(model, tokenizer, sequences, n_samples=100) → DataFrame`**
- For each attention head, compute which token types it most frequently attends to
- Aggregate across many sequences
- Returns a DataFrame: rows=heads, columns=token categories, values=avg attention weight

**`plot_head_specialization(head_roles_df) → Figure`**
- Heatmap: heads × token categories
- Reveals roles: "head 3/layer 2 is the rhythm head", "head 1/layer 5 is the instrument head"
- Unique to music transformers — educational about both transformers and music

### Tests

- `test_analyze_head_roles` — returns DataFrame with correct shape
- `test_plot_head_specialization` — returns Figure

---

## PR 5: Notebook refactor

After the module is built and tested:
1. Rewrite `notebooks/exploring_the_embedding.ipynb` to import from `jammy.analysis`
2. Fix hardcoded paths → use constants
3. Remove broken "NOT WORKING" cells
4. Replace "WORK IN PROGRESS" with the new attention/head analysis
5. Re-execute and render to HTML
6. Update `docs/exploring_the_embedding.html`

The notebook becomes thin:
```python
from jammy.analysis.embedding import plot_tsne, plot_embedding_comparison
from jammy.analysis.attention import plot_attention_heatmap, plot_layer_flow
from jammy.analysis.activation import plot_top_predictions
from jammy.analysis.head_roles import analyze_head_roles, plot_head_specialization

model = GPT2LMHeadModel.from_pretrained(MODEL_REPO, revision=MODEL_REVISION)
tokenizer = PreTrainedTokenizerFast.from_pretrained(MODEL_REPO, revision=MODEL_REVISION)

# Each cell is just a function call + display
fig = plot_tsne(model, tokenizer)
fig = plot_attention_heatmap(model, tokenizer, "PIECE_START TRACK_START INST=DRUMS ...")
```

---

## Shared utilities

All visualization functions should:
- Accept `model` and `tokenizer` as inputs (dependency injection, testable)
- Return `matplotlib.Figure` (not call `plt.show()`)
- Accept optional `output_path` to save to file
- Use consistent color scheme for token categories:
  - Structure (PIECE/TRACK/BAR): purple
  - Instruments (INST): blue
  - Notes (NOTE_ON/OFF): black
  - Time (TIME_DELTA): red
  - Density: green
  - Special ([UNK]/[PAD]/[MASK]): grey

Define these in `__init__.py`:
```python
TOKEN_COLORS = {
    "structure": "purple",
    "instrument": "blue",
    "note": "black",
    "time": "red",
    "density": "green",
    "special": "grey",
}

def categorize_token(token: str) -> str:
    """Categorize a token string into its type."""
    ...
```

---

## Execution Order

1. **PR 1**: embedding.py + tests (quick win, most visual impact)
2. **PR 2**: activation.py + tests
3. **PR 3**: attention.py + tests
4. **PR 4**: head_roles.py + tests (stretch)
5. **PR 5**: notebook refactor + re-render HTML

PRs 1-3 are independent and could be done in any order. PR 4 depends on 3 (uses attention data). PR 5 depends on all others.

---

## Dependencies

All functions need:
- `torch`, `transformers` — model inference
- `matplotlib` — static plots
- `numpy` — array operations
- `sklearn` — TSNE (already in [notebooks] optional group)

Optional (for interactive plots):
- `plotly` — hover labels on TSNE (add to [notebooks] if used)

No `bertviz` needed — we're building our own attention visualizations.
