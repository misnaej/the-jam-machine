"""Next-token prediction and activation visualizations.

Shows what the model predicts as the most likely next token at each
position in a sequence. Compares trained vs untrained to show how
training sharpens predictions into musically coherent choices.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go
import torch
from plotly.subplots import make_subplots

from jammy.analysis import (
    DEFAULT_SEQUENCE_MEDIUM,
    DEFAULT_SEQUENCE_SHORT,
    PLOTLY_JS,
    TOKEN_COLORS,
    categorize_token,
)

if TYPE_CHECKING:
    from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast


def plot_top_predictions(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequence: str | None = None,
    top_k: int = 10,
) -> str:
    """Plot the top-K predicted next tokens at each position in a sequence.

    For each token in the input, shows a horizontal bar chart of the most
    likely next tokens and their probabilities.

    Args:
        model: GPT-2 model.
        tokenizer: The tokenizer.
        sequence: Input token sequence. If None, uses a default example.
        top_k: Number of top predictions to show per position.

    Returns:
        HTML string containing the interactive plotly chart.
    """
    if sequence is None:
        sequence = DEFAULT_SEQUENCE_MEDIUM

    tokens = sequence.split(" ")
    inputs = tokenizer.encode(sequence, return_tensors="pt")

    with torch.no_grad():
        outputs = model(inputs)

    probs = torch.nn.functional.softmax(outputs["logits"][0], dim=-1)
    n_positions = len(tokens)

    fig = make_subplots(
        rows=n_positions,
        cols=1,
        subplot_titles=[f'After: "{t}"' for t in tokens],
        vertical_spacing=0.03,
    )

    for pos, _token in enumerate(tokens):
        position_probs = probs[pos].detach().numpy()
        top_indices = position_probs.argsort()[-top_k:][::-1]
        top_tokens = [tokenizer.decode(idx) for idx in top_indices]
        top_probs = [float(position_probs[idx]) for idx in top_indices]
        colors = [TOKEN_COLORS[categorize_token(t)] for t in top_tokens]

        # Reverse for plotly (bottom-to-top)
        fig.add_trace(
            go.Bar(
                x=top_probs[::-1],
                y=top_tokens[::-1],
                orientation="h",
                marker_color=colors[::-1],
                showlegend=False,
                hovertemplate="%{y}: %{x:.1%}<extra></extra>",
            ),
            row=pos + 1,
            col=1,
        )

    fig.update_layout(
        title="Top-K Next Token Predictions",
        height=200 * n_positions,
        width=950,
        template="plotly_white",
        margin={"l": 120},
    )
    for i in range(1, n_positions + 1):
        fig.update_xaxes(range=[0, 1], row=i, col=1)

    return fig.to_html(full_html=False, include_plotlyjs=PLOTLY_JS)


def plot_prediction_comparison(
    trained_model: GPT2LMHeadModel,
    untrained_model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequence: str | None = None,
    top_k: int = 8,
) -> str:
    """Side-by-side prediction comparison: trained vs untrained model.

    Shows how training makes predictions sharp and musically coherent,
    while the untrained model predicts near-uniform random tokens.

    Args:
        trained_model: Trained GPT-2 model.
        untrained_model: Untrained GPT-2 model (random weights).
        tokenizer: The tokenizer.
        sequence: Input token sequence. If None, uses a default example.
        top_k: Number of top predictions to show per position.

    Returns:
        HTML string containing the interactive plotly chart.
    """
    if sequence is None:
        sequence = DEFAULT_SEQUENCE_SHORT

    tokens = sequence.split(" ")
    inputs = tokenizer.encode(sequence, return_tensors="pt")
    n_positions = len(tokens)

    fig = make_subplots(
        rows=n_positions,
        cols=2,
        subplot_titles=[item for t in tokens for item in (f'Trained: "{t}"', f'Untrained: "{t}"')],
        horizontal_spacing=0.15,
        vertical_spacing=0.05,
    )

    for col, model_obj in enumerate(
        [trained_model, untrained_model],
        start=1,
    ):
        with torch.no_grad():
            outputs = model_obj(inputs)

        probs = torch.nn.functional.softmax(outputs["logits"][0], dim=-1)

        for pos in range(n_positions):
            position_probs = probs[pos].detach().numpy()
            top_indices = position_probs.argsort()[-top_k:][::-1]
            top_tokens = [tokenizer.decode(idx) for idx in top_indices]
            top_probs = [float(position_probs[idx]) for idx in top_indices]
            colors = [TOKEN_COLORS[categorize_token(t)] for t in top_tokens]

            fig.add_trace(
                go.Bar(
                    x=top_probs[::-1],
                    y=top_tokens[::-1],
                    orientation="h",
                    marker_color=colors[::-1],
                    showlegend=False,
                    hovertemplate="%{y}: %{x:.1%}<extra></extra>",
                ),
                row=pos + 1,
                col=col,
            )

    fig.update_layout(
        title="Next Token Predictions: Trained vs Untrained",
        height=200 * n_positions,
        width=950,
        template="plotly_white",
        margin={"l": 120},
    )
    for row in range(1, n_positions + 1):
        for col in range(1, 3):
            fig.update_xaxes(range=[0, 1], row=row, col=col)

    return fig.to_html(full_html=False, include_plotlyjs=PLOTLY_JS)
