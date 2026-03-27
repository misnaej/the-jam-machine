"""Attention head specialization analysis.

Discovers which attention heads specialize in tracking different aspects
of the music: some heads may focus on rhythm (TIME_DELTA tokens), others
on harmony (NOTE tokens), others on structure (BAR/TRACK tokens).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib
import matplotlib.pyplot as plt
import torch

from jammy.analysis import TOKEN_CATEGORY_ORDER, categorize_token

if TYPE_CHECKING:
    from pathlib import Path

    from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast

matplotlib.use("Agg")


def analyze_head_roles(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequences: list[str],
) -> dict[str, list[list[float]]]:
    """Compute average attention per token category for each head.

    For each attention head, measures how much attention it pays to each
    token category (structure, instrument, density, note, time, special)
    averaged across the provided sequences.

    Args:
        model: GPT-2 model.
        tokenizer: The tokenizer.
        sequences: List of token sequences to analyze.

    Returns:
        Dict with keys:
        - "weights": list of shape (n_layers, n_heads, n_categories)
        - "categories": list of category names
        - "n_layers": number of layers
        - "n_heads": number of heads per layer
    """
    category_names = TOKEN_CATEGORY_ORDER
    n_categories = len(category_names)

    # Accumulate attention weights across sequences
    weights_sum = None
    count = 0

    for sequence in sequences:
        inputs = tokenizer.encode(sequence, return_tensors="pt")
        token_list = [tokenizer.decode(t) for t in inputs[0]]
        token_cats = [categorize_token(t) for t in token_list]

        with torch.no_grad():
            outputs = model(inputs, output_attentions=True)

        if outputs.attentions is None or outputs.attentions[0] is None:
            msg = (
                "Model did not return attention weights. "
                "Load with: GPT2LMHeadModel.from_pretrained(..., attn_implementation='eager')"
            )
            raise RuntimeError(msg)

        attentions = outputs.attentions
        n_layers = len(attentions)
        n_heads = attentions[0].shape[1]
        seq_len = len(token_list)

        if weights_sum is None:
            weights_sum = [[[0.0] * n_categories for _ in range(n_heads)] for _ in range(n_layers)]

        # For each layer/head, sum attention weights by target category
        for layer_idx in range(n_layers):
            attn = attentions[layer_idx][0].detach().numpy()  # (heads, seq, seq)
            for head_idx in range(n_heads):
                head_attn = attn[head_idx]  # (seq, seq)
                # Average across all query positions
                avg_attn = head_attn.mean(axis=0)  # (seq,)
                for tok_idx in range(seq_len):
                    cat_idx = category_names.index(token_cats[tok_idx])
                    weights_sum[layer_idx][head_idx][cat_idx] += avg_attn[tok_idx]

        count += 1

    # Normalize
    if weights_sum and count > 0:
        for layer in weights_sum:
            for head in layer:
                total = sum(head)
                if total > 0:
                    for i in range(n_categories):
                        head[i] /= total

    return {
        "weights": weights_sum or [],
        "categories": category_names,
        "n_layers": n_layers,
        "n_heads": n_heads,
    }


def plot_head_specialization(
    head_roles: dict[str, list[list[float]]],
    output_path: Path | None = None,
) -> plt.Figure:
    """Plot a heatmap showing which token categories each head attends to.

    Rows = attention heads (grouped by layer), columns = token categories.
    Color intensity = proportion of attention paid to that category.
    Reveals head roles: "the rhythm head", "the instrument head", etc.

    Args:
        head_roles: Output from analyze_head_roles().
        output_path: If set, save the figure to this path.

    Returns:
        Matplotlib Figure.
    """
    weights = head_roles["weights"]
    categories = head_roles["categories"]
    n_layers = head_roles["n_layers"]
    n_heads = head_roles["n_heads"]

    # Build matrix: (n_layers * n_heads, n_categories)
    import numpy as np  # noqa: PLC0415

    matrix = np.zeros((n_layers * n_heads, len(categories)))
    labels = []
    for layer_idx in range(n_layers):
        for head_idx in range(n_heads):
            row = layer_idx * n_heads + head_idx
            matrix[row] = weights[layer_idx][head_idx]
            labels.append(f"L{layer_idx}H{head_idx}")

    fig, ax = plt.subplots(figsize=(8, max(6, n_layers * n_heads * 0.4)))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto", vmin=0)

    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels([c.capitalize() for c in categories], fontsize=9, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=7)

    # Add layer separators
    for layer_idx in range(1, n_layers):
        ax.axhline(layer_idx * n_heads - 0.5, color="black", linewidth=0.8)

    ax.set_xlabel("Token Category", fontsize=11)
    ax.set_ylabel("Attention Head", fontsize=11)
    ax.set_title("Head Specialization: What Each Head Attends To", fontsize=13)
    fig.colorbar(im, ax=ax, shrink=0.6, label="Attention proportion")
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, bbox_inches="tight", dpi=150)
    return fig


def plot_head_comparison(
    head_roles: dict[str, list[list[float]]],
    output_path: Path | None = None,
) -> plt.Figure:
    """Compare the two most differently-specialized heads.

    Finds the pair of heads with the most divergent attention profiles
    and plots them side by side as bar charts. Adds a text summary
    explaining what each head focuses on.

    Args:
        head_roles: Output from analyze_head_roles().
        output_path: If set, save the figure to this path.

    Returns:
        Matplotlib Figure.
    """
    import numpy as np  # noqa: PLC0415

    weights = head_roles["weights"]
    categories = head_roles["categories"]
    n_layers = head_roles["n_layers"]
    n_heads = head_roles["n_heads"]

    # Flatten all heads into a list of (label, weight_vector) pairs
    heads: list[tuple[str, list[float]]] = []
    for layer_idx in range(n_layers):
        for head_idx in range(n_heads):
            label = f"Layer {layer_idx}, Head {head_idx}"
            heads.append((label, weights[layer_idx][head_idx]))

    # Find the pair with maximum cosine distance
    max_dist = -1.0
    best_pair = (0, 1)
    for i in range(len(heads)):
        for j in range(i + 1, len(heads)):
            vi = np.array(heads[i][1])
            vj = np.array(heads[j][1])
            norm_i = np.linalg.norm(vi)
            norm_j = np.linalg.norm(vj)
            if norm_i > 0 and norm_j > 0:
                cos_sim = np.dot(vi, vj) / (norm_i * norm_j)
                dist = 1 - cos_sim
                if dist > max_dist:
                    max_dist = dist
                    best_pair = (i, j)

    head_a_label, head_a_weights = heads[best_pair[0]]
    head_b_label, head_b_weights = heads[best_pair[1]]

    # Describe what each head focuses on
    cat_labels = [c.capitalize() for c in categories]

    def _describe(w: list[float]) -> str:
        top_idx = int(np.argmax(w))
        top_pct = w[top_idx] * 100
        return f"Focuses on {categories[top_idx]} tokens ({top_pct:.0f}%)"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4), sharey=True)

    from jammy.analysis import TOKEN_COLORS  # noqa: PLC0415

    colors = [TOKEN_COLORS[c] for c in categories]

    ax1.barh(range(len(categories)), head_a_weights, color=colors, height=0.6)
    ax1.set_yticks(range(len(categories)))
    ax1.set_yticklabels(cat_labels, fontsize=10)
    ax1.invert_yaxis()
    ax1.set_title(head_a_label, fontsize=11, fontweight="bold")
    ax1.set_xlabel("Attention proportion")
    ax1.annotate(
        _describe(head_a_weights),
        xy=(0.5, 0),
        xycoords="axes fraction",
        xytext=(0, -25),
        textcoords="offset points",
        fontsize=9,
        style="italic",
        ha="center",
    )

    ax2.barh(range(len(categories)), head_b_weights, color=colors, height=0.6)
    ax2.set_title(head_b_label, fontsize=11, fontweight="bold")
    ax2.set_xlabel("Attention proportion")
    ax2.annotate(
        _describe(head_b_weights),
        xy=(0.5, 0),
        xycoords="axes fraction",
        xytext=(0, -25),
        textcoords="offset points",
        fontsize=9,
        style="italic",
        ha="center",
    )

    fig.suptitle("Most Differently Specialized Heads", fontsize=13)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.15)

    if output_path:
        fig.savefig(output_path, bbox_inches="tight", dpi=150)
    return fig
