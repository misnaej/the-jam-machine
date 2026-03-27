"""Attention pattern visualizations.

Shows what tokens the model pays attention to at each layer and head.
Reveals how the transformer builds understanding of musical structure:
early layers attend to local context, later layers attend to global
structure like instrument identity and bar boundaries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib
import matplotlib.pyplot as plt
import torch

if TYPE_CHECKING:
    from pathlib import Path

    from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast

matplotlib.use("Agg")


def _get_attention(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequence: str,
) -> tuple[tuple, list[str]]:
    """Run a forward pass and extract attention weights.

    Args:
        model: GPT-2 model (must have output_attentions=True).
        tokenizer: The tokenizer.
        sequence: Input token sequence as a string.

    Returns:
        Tuple of (attention_tuple, token_list).
        attention_tuple has shape (n_layers,) where each element is
        (batch, n_heads, seq_len, seq_len).
    """
    inputs = tokenizer.encode(sequence, return_tensors="pt")
    token_list = [tokenizer.decode(t) for t in inputs[0]]

    with torch.no_grad():
        outputs = model(inputs, output_attentions=True)

    return outputs.attentions, token_list


def plot_attention_heatmap(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequence: str | None = None,
    layer: int | None = None,
    output_path: Path | None = None,
) -> plt.Figure:
    """Plot attention weights as heatmaps.

    Each cell (i, j) shows how much token i attends to token j.
    If layer is None, averages across all heads and shows all layers.
    If layer is specified, shows all heads for that layer.

    Args:
        model: GPT-2 model.
        tokenizer: The tokenizer.
        sequence: Input token sequence. If None, uses a default example.
        layer: Which layer to show (0-indexed). None = all layers averaged.
        output_path: If set, save the figure to this path.

    Returns:
        Matplotlib Figure.
    """
    if sequence is None:
        sequence = (
            "PIECE_START TRACK_START INST=DRUMS DENSITY=2"
            " BAR_START NOTE_ON=36 TIME_DELTA=2 NOTE_OFF=36"
        )

    attentions, token_list = _get_attention(model, tokenizer, sequence)
    n_layers = len(attentions)

    if layer is not None:
        # Show all heads for one layer
        attn = attentions[layer][0].detach().numpy()  # (n_heads, seq, seq)
        n_heads = attn.shape[0]
        cols = min(4, n_heads)
        rows = (n_heads + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 3.5 * rows))
        axes = axes.flatten() if n_heads > 1 else [axes]

        for h in range(n_heads):
            ax = axes[h]
            ax.imshow(attn[h], cmap="Blues", vmin=0, vmax=1)
            ax.set_xticks(range(len(token_list)))
            ax.set_xticklabels(token_list, rotation=45, ha="right", fontsize=6)
            ax.set_yticks(range(len(token_list)))
            ax.set_yticklabels(token_list, fontsize=6)
            ax.set_title(f"Head {h}", fontsize=9)

        for h in range(n_heads, len(axes)):
            axes[h].set_visible(False)

        fig.suptitle(f"Attention Weights — Layer {layer}", fontsize=13)
    else:
        # Show all layers, averaged across heads
        cols = min(3, n_layers)
        rows = (n_layers + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 4 * rows))
        axes = axes.flatten() if n_layers > 1 else [axes]

        for layer_idx in range(n_layers):
            ax = axes[layer_idx]
            attn = attentions[layer_idx][0].mean(dim=0).detach().numpy()
            ax.imshow(attn, cmap="Blues", vmin=0, vmax=attn.max())
            ax.set_xticks(range(len(token_list)))
            ax.set_xticklabels(token_list, rotation=45, ha="right", fontsize=6)
            ax.set_yticks(range(len(token_list)))
            ax.set_yticklabels(token_list, fontsize=6)
            ax.set_title(f"Layer {layer_idx}", fontsize=10)

        for idx in range(n_layers, len(axes)):
            axes[idx].set_visible(False)

        fig.suptitle("Attention Weights (averaged across heads)", fontsize=13)

    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, bbox_inches="tight", dpi=150)
    return fig


def plot_layer_flow(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequence: str | None = None,
    target_position: int = -1,
    output_path: Path | None = None,
) -> plt.Figure:
    """Show how attention builds up across layers for a target token.

    For a single target token position, shows which source tokens it
    attends to at each layer (averaged across heads). Reveals how
    information flows: early layers attend locally, later layers
    attend to structural tokens (INST, BAR_START).

    Args:
        model: GPT-2 model.
        tokenizer: The tokenizer.
        sequence: Input token sequence. If None, uses a default example.
        target_position: Which token to analyze (-1 = last token).
        output_path: If set, save the figure to this path.

    Returns:
        Matplotlib Figure.
    """
    if sequence is None:
        sequence = (
            "PIECE_START TRACK_START INST=DRUMS DENSITY=2"
            " BAR_START NOTE_ON=36 TIME_DELTA=2 NOTE_OFF=36"
        )

    attentions, token_list = _get_attention(model, tokenizer, sequence)
    n_layers = len(attentions)
    seq_len = len(token_list)

    if target_position < 0:
        target_position = seq_len + target_position

    # Build matrix: (n_layers, seq_len) — attention from target to each source
    flow = []
    for layer_idx in range(n_layers):
        attn = attentions[layer_idx][0].mean(dim=0).detach().numpy()
        flow.append(attn[target_position, :])

    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(flow, cmap="Blues", aspect="auto")

    ax.set_yticks(range(n_layers))
    ax.set_yticklabels([f"Layer {i}" for i in range(n_layers)], fontsize=9)
    ax.set_xticks(range(seq_len))
    ax.set_xticklabels(token_list, rotation=45, ha="right", fontsize=8)
    ax.set_xlabel("Source token", fontsize=11)
    ax.set_ylabel("Layer", fontsize=11)

    target_name = token_list[target_position]
    ax.set_title(
        f'Attention flow to "{target_name}" (position {target_position})',
        fontsize=12,
    )
    fig.colorbar(im, ax=ax, shrink=0.8, label="Attention weight")
    fig.tight_layout()

    if output_path:
        fig.savefig(output_path, bbox_inches="tight", dpi=150)
    return fig
