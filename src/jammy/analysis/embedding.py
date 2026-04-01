"""Token embedding visualizations.

Visualize how the GPT-2 model represents MIDI tokens in its embedding space.
Includes heatmaps of the raw embedding matrix and TSNE dimensionality reduction
to show how similar tokens cluster together after training.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go
from sklearn.manifold import TSNE

from jammy.analysis import PLOTLY_JS, TOKEN_CATEGORY_ORDER, TOKEN_COLORS, categorize_token

if TYPE_CHECKING:
    import numpy as np
    from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast


def _get_embedding(model: GPT2LMHeadModel) -> np.ndarray:
    """Extract the token embedding matrix from the model.

    Args:
        model: GPT-2 model.

    Returns:
        Numpy array of shape (vocab_size, embedding_dim).
    """
    return model.get_input_embeddings().state_dict()["weight"].detach().numpy()  # type: ignore[no-any-return]


def _get_token_list(tokenizer: PreTrainedTokenizerFast) -> list[str]:
    """Get all tokens in vocabulary order.

    Args:
        tokenizer: The tokenizer.

    Returns:
        List of token strings, indexed by token ID.
    """
    return [str(tokenizer.decode(i)) for i in range(tokenizer.vocab_size)]


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


def _embedding_heatmap_plotly(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    title: str,
    zmin: float | None = None,
    zmax: float | None = None,
) -> go.Figure:
    """Create a plotly heatmap of the embedding matrix.

    Tokens are sorted by category and displayed on the x-axis,
    embedding dimensions on the y-axis.

    Args:
        model: GPT-2 model.
        tokenizer: The tokenizer.
        title: Plot title.
        zmin: Minimum value for the color scale.
        zmax: Maximum value for the color scale.

    Returns:
        Plotly Figure.
    """
    embedding = _get_embedding(model)
    tokens = _get_token_list(tokenizer)
    indices, sorted_tokens, categories = _sort_by_category(tokens)

    sorted_embedding = embedding[indices].T  # dims x tokens

    # Build category boundary shapes and annotations
    cat_positions: dict[str, list[int]] = {}
    for i, cat in enumerate(categories):
        cat_positions.setdefault(cat, []).append(i)

    shapes = []
    annotations = []
    for cat, positions in cat_positions.items():
        mid = positions[len(positions) // 2]
        annotations.append(
            {
                "x": mid,
                "y": -0.08,
                "xref": "x",
                "yref": "paper",
                "text": f"<b>{cat.capitalize()}</b>",
                "showarrow": False,
                "font": {"size": 11, "color": TOKEN_COLORS[cat]},
                "textangle": -45,
                "xanchor": "left",
                "yanchor": "top",
            },
        )
        # Thick horizontal bar at the bottom spanning the category
        shapes.append(
            {
                "type": "line",
                "x0": positions[0] - 0.5,
                "x1": positions[-1] + 0.5,
                "y0": -0.01,
                "y1": -0.01,
                "yref": "paper",
                "line": {
                    "color": TOKEN_COLORS[cat],
                    "width": 4,
                },
            },
        )

    fig = go.Figure(
        data=go.Heatmap(
            z=sorted_embedding.tolist(),
            x=sorted_tokens,
            colorscale="Blues",
            zmin=zmin,
            zmax=zmax,
            showscale=True,
            colorbar={"title": "Value", "thickness": 15},
            hovertemplate="Token: %{x}<br>Dim: %{y}<br>Value: %{z:.3f}<extra></extra>",
        ),
    )
    fig.update_layout(
        title={"text": title, "font": {"size": 14}},
        xaxis={
            "showticklabels": False,
            "title": "",
        },
        yaxis={"title": "Embedding dimension"},
        width=950,
        height=500,
        template="plotly_white",
        margin={"b": 120, "t": 50},
        shapes=shapes,
        annotations=annotations,
    )
    return fig


def plot_embedding_heatmap_comparison(
    trained_model: GPT2LMHeadModel,
    untrained_model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
) -> tuple[str, str]:
    """Separate embedding heatmaps for trained vs untrained models.

    Each figure shows the transposed embedding matrix (dimensions x tokens)
    so they can be stacked vertically with tokens aligned.

    Args:
        trained_model: Trained GPT-2 model.
        untrained_model: Untrained GPT-2 model (random weights).
        tokenizer: The tokenizer.

    Returns:
        Tuple of (trained_html, untrained_html).
    """
    # Compute shared z-axis limits for visual comparison
    trained_emb = _get_embedding(trained_model)
    untrained_emb = _get_embedding(untrained_model)
    zmin = min(float(trained_emb.min()), float(untrained_emb.min()))
    zmax = max(float(trained_emb.max()), float(untrained_emb.max()))

    trained_html = _embedding_heatmap_plotly(
        trained_model,
        tokenizer,
        "Trained Model",
        zmin=zmin,
        zmax=zmax,
    ).to_html(full_html=False, include_plotlyjs=PLOTLY_JS)
    untrained_html = _embedding_heatmap_plotly(
        untrained_model,
        tokenizer,
        "Untrained Model (Random Weights)",
        zmin=zmin,
        zmax=zmax,
    ).to_html(full_html=False, include_plotlyjs=PLOTLY_JS)
    return trained_html, untrained_html


def _tsne_plotly(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    title: str,
    random_state: int = 42,
) -> go.Figure:
    """Create an interactive plotly TSNE scatter plot.

    Each point shows the token text on hover.

    Args:
        model: GPT-2 model.
        tokenizer: The tokenizer.
        title: Plot title.
        random_state: Random seed for reproducibility.

    Returns:
        Plotly Figure.
    """
    embedding = _get_embedding(model)
    tokens = _get_token_list(tokenizer)

    perplexity = min(30, len(embedding) - 1)
    tsne = TSNE(
        n_components=2,
        random_state=random_state,
        perplexity=perplexity,
    )
    coords = tsne.fit_transform(embedding)

    fig = go.Figure()
    for cat in TOKEN_CATEGORY_ORDER:
        mask = [i for i, t in enumerate(tokens) if categorize_token(t) == cat]
        if mask:
            fig.add_trace(
                go.Scatter(
                    x=coords[mask, 0].tolist(),
                    y=coords[mask, 1].tolist(),
                    mode="markers",
                    name=cat.capitalize(),
                    text=[tokens[i] for i in mask],
                    hovertemplate="%{text}<extra></extra>",
                    marker={
                        "size": 7,
                        "color": TOKEN_COLORS[cat],
                        "opacity": 0.7,
                    },
                ),
            )

    fig.update_layout(
        title=title,
        xaxis_title="TSNE 1",
        yaxis_title="TSNE 2",
        width=950,
        height=600,
        template="plotly_white",
        legend={"font": {"size": 11}},
    )
    return fig


def plot_tsne(
    trained_model: GPT2LMHeadModel,
    untrained_model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    random_state: int = 42,
) -> tuple[str, str]:
    """Interactive TSNE plots: trained vs untrained embeddings.

    Returns two separate plotly HTML strings that can be stacked vertically.
    Hover over any point to see the token name.

    Args:
        trained_model: Trained GPT-2 model.
        untrained_model: Untrained GPT-2 model (random weights).
        tokenizer: The tokenizer.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (trained_html, untrained_html).
    """
    trained_html = _tsne_plotly(
        trained_model,
        tokenizer,
        "Trained Model",
        random_state,
    ).to_html(full_html=False, include_plotlyjs=PLOTLY_JS)
    untrained_html = _tsne_plotly(
        untrained_model,
        tokenizer,
        "Untrained Model (Random Weights)",
        random_state,
    ).to_html(full_html=False, include_plotlyjs=PLOTLY_JS)
    return trained_html, untrained_html
