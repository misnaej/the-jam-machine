"""Attention head specialization analysis.

Discovers which attention heads specialize in tracking different aspects
of the music: some heads may focus on rhythm (TIME_DELTA tokens), others
on harmony (NOTE tokens), others on structure (BAR/TRACK tokens).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

import numpy as np
import plotly.graph_objects as go
import torch
from plotly.subplots import make_subplots

from jammy.analysis import PLOTLY_JS, TOKEN_CATEGORY_ORDER, TOKEN_COLORS, categorize_token

if TYPE_CHECKING:
    from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast


class HeadRoles(TypedDict):
    """Result of head role analysis."""

    weights: list[list[list[float]]]
    categories: list[str]
    n_layers: int
    n_heads: int


def _accumulate_attention(
    attentions: tuple,
    token_cats: list[str],
    category_names: list[str],
    weights_sum: list[list[list[float]]],
) -> None:
    """Add attention weights by category to the running sum.

    Args:
        attentions: Model attention outputs (n_layers,).
        token_cats: Category for each token in the sequence.
        category_names: Ordered list of category names.
        weights_sum: Mutable accumulator (n_layers x n_heads x n_categories).
    """
    for layer_idx in range(len(attentions)):
        attn = attentions[layer_idx][0].detach().numpy()
        for head_idx in range(attn.shape[0]):
            avg_attn = attn[head_idx].mean(axis=0)
            for tok_idx, cat in enumerate(token_cats):
                cat_idx = category_names.index(cat)
                weights_sum[layer_idx][head_idx][cat_idx] += avg_attn[tok_idx]


def _normalize_weights(weights: list[list[list[float]]]) -> None:
    """Normalize each head's category weights to sum to 1.

    Args:
        weights: Mutable weights (n_layers x n_heads x n_categories).
    """
    for layer in weights:
        for head in layer:
            total = sum(head)
            if total > 0:
                head[:] = [w / total for w in head]


def analyze_head_roles(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequences: list[str],
) -> HeadRoles:
    """Compute average attention per token category for each head.

    For each attention head, measures how much attention it pays to each
    token category (structure, instrument, density, note, time, special)
    averaged across the provided sequences.

    Args:
        model: GPT-2 model.
        tokenizer: The tokenizer.
        sequences: List of token sequences to analyze.

    Returns:
        HeadRoles dict with keys: weights (n_layers x n_heads x n_categories),
        categories, n_layers, n_heads.
    """
    category_names = TOKEN_CATEGORY_ORDER
    n_categories = len(category_names)
    weights_sum = None
    n_layers = 0
    n_heads = 0

    for sequence in sequences:
        inputs = tokenizer.encode(sequence, return_tensors="pt")
        token_cats = [categorize_token(tokenizer.decode(t)) for t in inputs[0]]

        with torch.no_grad():
            outputs = model(inputs, output_attentions=True)

        if outputs.attentions is None or outputs.attentions[0] is None:
            msg = (
                "Model did not return attention weights. "
                "Load with: GPT2LMHeadModel.from_pretrained("
                "..., attn_implementation='eager')"
            )
            raise RuntimeError(msg)

        attentions = outputs.attentions
        n_layers = len(attentions)
        n_heads = attentions[0].shape[1]

        if weights_sum is None:
            weights_sum = [[[0.0] * n_categories for _ in range(n_heads)] for _ in range(n_layers)]

        _accumulate_attention(attentions, token_cats, category_names, weights_sum)

    if weights_sum:
        _normalize_weights(weights_sum)

    return {
        "weights": weights_sum or [],
        "categories": category_names,
        "n_layers": n_layers,
        "n_heads": n_heads,
    }


def plot_head_comparison(
    head_roles: HeadRoles,
) -> str:
    """Compare the two most differently-specialized heads.

    Finds the pair of heads with the most divergent attention profiles
    and plots them side by side as bar charts.

    Args:
        head_roles: Output from analyze_head_roles().

    Returns:
        HTML string containing the interactive plotly chart.
    """
    weights = head_roles["weights"]
    categories = head_roles["categories"]
    n_layers = head_roles["n_layers"]
    n_heads = head_roles["n_heads"]

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

    cat_labels = [c.capitalize() for c in categories]
    colors = [TOKEN_COLORS[c] for c in categories]

    def _describe(w: list[float]) -> str:
        top_idx = int(np.argmax(w))
        top_pct = w[top_idx] * 100
        return f"Focuses on {categories[top_idx]} ({top_pct:.0f}%)"

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[
            f"{head_a_label} — {_describe(head_a_weights)}",
            f"{head_b_label} — {_describe(head_b_weights)}",
        ],
        horizontal_spacing=0.15,
    )

    for col, w in enumerate([head_a_weights, head_b_weights], start=1):
        fig.add_trace(
            go.Bar(
                x=list(w)[::-1],
                y=cat_labels[::-1],
                orientation="h",
                marker_color=colors[::-1],
                showlegend=False,
                hovertemplate="%{y}: %{x:.1%}<extra></extra>",
            ),
            row=1,
            col=col,
        )

    fig.update_layout(
        title="Most Differently Specialized Heads",
        width=950,
        height=350,
        template="plotly_white",
    )
    return fig.to_html(full_html=False, include_plotlyjs=PLOTLY_JS)
