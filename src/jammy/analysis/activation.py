"""Next-token prediction and activation visualizations.

Shows what the model predicts as the most likely next token at each
position in a sequence. Compares trained vs untrained to show how
training sharpens predictions into musically coherent choices.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib
import matplotlib.pyplot as plt
import torch

from jammy.analysis import TOKEN_COLORS, categorize_token

if TYPE_CHECKING:
    from pathlib import Path

    from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast

matplotlib.use("Agg")


def plot_top_predictions(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequence: str | None = None,
    top_k: int = 10,
    output_path: Path | None = None,
) -> plt.Figure:
    """Plot the top-K predicted next tokens at each position in a sequence.

    For each token in the input, shows a horizontal bar chart of the most
    likely next tokens and their probabilities. This reveals what the model
    has learned about musical structure — e.g., after INST=DRUMS it predicts
    DENSITY tokens, after BAR_START it predicts NOTE_ON or TIME_DELTA.

    Args:
        model: GPT-2 model.
        tokenizer: The tokenizer.
        sequence: Input token sequence. If None, uses a default example.
        top_k: Number of top predictions to show per position.
        output_path: If set, save the figure to this path.

    Returns:
        Matplotlib Figure.
    """
    if sequence is None:
        sequence = (
            "PIECE_START TRACK_START INST=DRUMS DENSITY=2"
            " BAR_START NOTE_ON=36 TIME_DELTA=2 NOTE_OFF=36"
        )

    tokens = sequence.split(" ")
    inputs = tokenizer.encode(sequence, return_tensors="pt")

    with torch.no_grad():
        outputs = model(inputs)

    logits = outputs["logits"]
    probs = torch.nn.functional.softmax(logits[0], dim=-1)

    n_positions = len(tokens)
    fig, axes = plt.subplots(n_positions, 1, figsize=(8, 2.2 * n_positions))
    if n_positions == 1:
        axes = [axes]

    for pos, (ax, token) in enumerate(zip(axes, tokens, strict=True)):
        position_probs = probs[pos].detach().numpy()
        top_indices = position_probs.argsort()[-top_k:][::-1]
        top_tokens = [tokenizer.decode(idx) for idx in top_indices]
        top_probs = [position_probs[idx] for idx in top_indices]
        colors = [TOKEN_COLORS[categorize_token(t)] for t in top_tokens]

        y_pos = range(top_k)
        ax.barh(y_pos, top_probs, color=colors, height=0.7)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(top_tokens, fontsize=8)
        ax.invert_yaxis()
        ax.set_xlim(0, min(1.0, max(top_probs) * 1.3))
        ax.set_title(f'After: "{token}"', fontsize=9, loc="left", fontweight="bold")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.suptitle("Top-K Next Token Predictions", fontsize=13, y=1.01)
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, bbox_inches="tight", dpi=150)
    return fig


def plot_prediction_comparison(
    trained_model: GPT2LMHeadModel,
    untrained_model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequence: str | None = None,
    top_k: int = 8,
    output_path: Path | None = None,
) -> plt.Figure:
    """Side-by-side prediction comparison: trained vs untrained model.

    Shows how training makes predictions sharp and musically coherent,
    while the untrained model predicts near-uniform random tokens.

    Args:
        trained_model: Trained GPT-2 model.
        untrained_model: Untrained GPT-2 model (random weights).
        tokenizer: The tokenizer.
        sequence: Input token sequence. If None, uses a default example.
        top_k: Number of top predictions to show per position.
        output_path: If set, save the figure to this path.

    Returns:
        Matplotlib Figure.
    """
    if sequence is None:
        sequence = "PIECE_START TRACK_START INST=DRUMS DENSITY=2 BAR_START"

    tokens = sequence.split(" ")
    inputs = tokenizer.encode(sequence, return_tensors="pt")
    n_positions = len(tokens)

    fig, axes = plt.subplots(n_positions, 2, figsize=(14, 2.2 * n_positions))
    if n_positions == 1:
        axes = axes.reshape(1, 2)

    for col, (model_obj, title) in enumerate(
        [
            (trained_model, "Trained"),
            (untrained_model, "Untrained"),
        ],
    ):
        with torch.no_grad():
            outputs = model_obj(inputs)

        probs = torch.nn.functional.softmax(outputs["logits"][0], dim=-1)

        for pos, token in enumerate(tokens):
            ax = axes[pos, col]
            position_probs = probs[pos].detach().numpy()
            top_indices = position_probs.argsort()[-top_k:][::-1]
            top_tokens = [tokenizer.decode(idx) for idx in top_indices]
            top_probs = [position_probs[idx] for idx in top_indices]
            colors = [TOKEN_COLORS[categorize_token(t)] for t in top_tokens]

            y_pos = range(top_k)
            ax.barh(y_pos, top_probs, color=colors, height=0.7)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(top_tokens, fontsize=7)
            ax.invert_yaxis()
            ax.set_xlim(0, min(1.0, max(top_probs) * 1.3))
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            if col == 0:
                ax.set_ylabel(f'"{token}"', fontsize=8, fontweight="bold")
            if pos == 0:
                ax.set_title(title, fontsize=11, fontweight="bold")

    fig.suptitle("Next Token Predictions: Trained vs Untrained", fontsize=13, y=1.01)
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, bbox_inches="tight", dpi=150)
    return fig
