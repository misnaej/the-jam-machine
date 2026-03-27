"""Token embedding visualizations.

Visualize how the GPT-2 model represents MIDI tokens in its embedding space.
Includes heatmaps of the raw embedding matrix and TSNE dimensionality reduction
to show how similar tokens cluster together after training.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

from jammy.analysis import TOKEN_CATEGORY_ORDER, TOKEN_COLORS, categorize_token

if TYPE_CHECKING:
    from pathlib import Path

    import numpy as np
    from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast

matplotlib.use("Agg")


def _get_embedding(model: GPT2LMHeadModel) -> np.ndarray:
    """Extract the token embedding matrix from the model.

    Args:
        model: GPT-2 model.

    Returns:
        Numpy array of shape (vocab_size, embedding_dim).
    """
    return model.get_input_embeddings().state_dict()["weight"].detach().numpy()


def _get_token_list(tokenizer: PreTrainedTokenizerFast) -> list[str]:
    """Get all tokens in vocabulary order.

    Args:
        tokenizer: The tokenizer.

    Returns:
        List of token strings, indexed by token ID.
    """
    return [tokenizer.decode(i) for i in range(tokenizer.vocab_size)]


def _sort_by_category(
    tokens: list[str],
) -> tuple[list[int], list[str], list[str]]:
    """Sort token indices by category, then alphabetically within category.

    Args:
        tokens: List of token strings.

    Returns:
        Tuple of (sorted_indices, sorted_tokens, sorted_categories).
    """
    indexed = [(i, t, categorize_token(t)) for i, t in enumerate(tokens)]
    indexed.sort(key=lambda x: (TOKEN_CATEGORY_ORDER.index(x[2]), x[1]))
    indices = [x[0] for x in indexed]
    sorted_tokens = [x[1] for x in indexed]
    categories = [x[2] for x in indexed]
    return indices, sorted_tokens, categories


def plot_embedding_heatmap(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    output_path: Path | None = None,
) -> plt.Figure:
    """Plot the embedding matrix as a heatmap, grouped by token category.

    Tokens are sorted by category (structure, instruments, density, notes,
    time, special) so patterns within each group are visible.

    Args:
        model: GPT-2 model.
        tokenizer: The tokenizer.
        output_path: If set, save the figure to this path.

    Returns:
        Matplotlib Figure.
    """
    embedding = _get_embedding(model)
    tokens = _get_token_list(tokenizer)
    indices, _sorted_tokens, categories = _sort_by_category(tokens)

    sorted_embedding = embedding[indices]

    fig, ax = plt.subplots(figsize=(14, 10))
    im = ax.imshow(sorted_embedding, aspect="auto", cmap="inferno")

    # Add category color bar on the left
    for i, cat in enumerate(categories):
        ax.plot(-2, i, "s", color=TOKEN_COLORS[cat], markersize=3)

    # Add category boundaries
    prev_cat = categories[0]
    for i, cat in enumerate(categories):
        if cat != prev_cat:
            ax.axhline(i - 0.5, color="white", linewidth=0.8, alpha=0.7)
            prev_cat = cat

    # Add category labels
    cat_positions: dict[str, list[int]] = {}
    for i, cat in enumerate(categories):
        cat_positions.setdefault(cat, []).append(i)
    for cat, positions in cat_positions.items():
        mid = positions[len(positions) // 2]
        ax.text(
            -8,
            mid,
            cat.capitalize(),
            fontsize=9,
            color=TOKEN_COLORS[cat],
            ha="right",
            va="center",
            fontweight="bold",
        )

    ax.set_xlabel("Embedding dimension", fontsize=11)
    ax.set_ylabel("Token (grouped by category)", fontsize=11)
    ax.set_yticks([])
    ax.set_title("Token Embedding Matrix", fontsize=13)
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, bbox_inches="tight", dpi=150)
    return fig


def plot_tsne(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    output_path: Path | None = None,
    random_state: int = 42,
) -> plt.Figure:
    """Plot TSNE dimensionality reduction of the embedding space.

    Reduces 512-dimensional embeddings to 2D. Similar tokens cluster together:
    notes form one region, instruments another, time steps another.

    Args:
        model: GPT-2 model.
        tokenizer: The tokenizer.
        output_path: If set, save the figure to this path.
        random_state: Random seed for reproducibility.

    Returns:
        Matplotlib Figure.
    """
    embedding = _get_embedding(model)
    tokens = _get_token_list(tokenizer)

    perplexity = min(30, len(embedding) - 1)
    tsne = TSNE(n_components=2, random_state=random_state, perplexity=perplexity)
    coords = tsne.fit_transform(embedding)

    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot each category separately for legend
    plotted_categories: set[str] = set()
    for i, token in enumerate(tokens):
        cat = categorize_token(token)
        label = cat.capitalize() if cat not in plotted_categories else None
        plotted_categories.add(cat)
        ax.scatter(
            coords[i, 0],
            coords[i, 1],
            s=20,
            color=TOKEN_COLORS[cat],
            label=label,
            alpha=0.7,
        )

    ax.legend(fontsize=10, loc="upper right")
    ax.set_xlabel("TSNE 1", fontsize=11)
    ax.set_ylabel("TSNE 2", fontsize=11)
    ax.set_title("Token Embedding Space (TSNE)", fontsize=13)
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, bbox_inches="tight", dpi=150)
    return fig


def plot_embedding_comparison(
    trained_model: GPT2LMHeadModel,
    untrained_model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    output_path: Path | None = None,
    random_state: int = 42,
) -> plt.Figure:
    """Side-by-side TSNE comparison of trained vs untrained embeddings.

    Shows how training organizes the embedding space — trained model clusters
    similar tokens together, untrained model is random noise.

    Args:
        trained_model: Trained GPT-2 model.
        untrained_model: Untrained GPT-2 model (random weights).
        tokenizer: The tokenizer.
        output_path: If set, save the figure to this path.
        random_state: Random seed for reproducibility.

    Returns:
        Matplotlib Figure with 2 subplots.
    """
    tokens = _get_token_list(tokenizer)
    perplexity = min(30, len(tokens) - 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

    for ax, model_obj, title in [
        (ax1, trained_model, "Trained Model"),
        (ax2, untrained_model, "Untrained Model (Random Weights)"),
    ]:
        embedding = _get_embedding(model_obj)
        tsne = TSNE(n_components=2, random_state=random_state, perplexity=perplexity)
        coords = tsne.fit_transform(embedding)

        plotted: set[str] = set()
        for i, token in enumerate(tokens):
            cat = categorize_token(token)
            label = cat.capitalize() if cat not in plotted else None
            plotted.add(cat)
            ax.scatter(
                coords[i, 0],
                coords[i, 1],
                s=20,
                color=TOKEN_COLORS[cat],
                label=label,
                alpha=0.7,
            )

        ax.legend(fontsize=9, loc="upper right")
        ax.set_title(title, fontsize=12)
        ax.set_xlabel("TSNE 1")
        ax.set_ylabel("TSNE 2")

    fig.suptitle("Embedding Space: Trained vs Untrained", fontsize=14, y=1.02)
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, bbox_inches="tight", dpi=150)
    return fig
