"""Attention pattern visualizations.

Shows what tokens the model pays attention to at each layer and head.
Reveals how the transformer builds understanding of musical structure:
early layers attend to local context, later layers attend to global
structure like instrument identity and bar boundaries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import plotly.graph_objects as go
import torch
from plotly.subplots import make_subplots

from jammy.analysis import DEFAULT_SEQUENCE_LONG, PLOTLY_JS, TOKEN_COLORS, categorize_token

if TYPE_CHECKING:
    from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast


def _get_attention(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequence: str,
) -> tuple[tuple, list[str]]:
    """Run a forward pass and extract attention weights.

    The model must be loaded with ``attn_implementation='eager'`` because
    PyTorch's SDPA fuses the attention computation into a single kernel
    that doesn't expose intermediate attention weights.

    Args:
        model: GPT-2 model loaded with ``attn_implementation='eager'``.
        tokenizer: The tokenizer.
        sequence: Input token sequence as a string.

    Returns:
        Tuple of (attention_tuple, token_list).

    Raises:
        RuntimeError: If the model doesn't return attention weights.
    """
    inputs = tokenizer.encode(sequence, return_tensors="pt")
    token_list = [tokenizer.decode(t) for t in inputs[0]]

    with torch.no_grad():
        outputs = model(inputs, output_attentions=True)

    if outputs.attentions is None or outputs.attentions[0] is None:
        msg = (
            "Model did not return attention weights. "
            "Load with: GPT2LMHeadModel.from_pretrained("
            "..., attn_implementation='eager')"
        )
        raise RuntimeError(msg)

    return outputs.attentions, token_list


def plot_attention_comparison(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequence: str | None = None,
) -> str:
    """Side-by-side attention heatmaps: first layer vs last layer.

    Shows how attention patterns sharpen across depth.

    Args:
        model: GPT-2 model loaded with ``attn_implementation='eager'``.
        tokenizer: The tokenizer.
        sequence: Input token sequence. If None, uses a 12-token example.

    Returns:
        HTML string containing the interactive plotly chart.
    """
    if sequence is None:
        sequence = DEFAULT_SEQUENCE_LONG

    attentions, token_list = _get_attention(model, tokenizer, sequence)
    n_layers = len(attentions)

    early_attn = attentions[0][0].mean(dim=0).detach().numpy()
    late_attn = attentions[n_layers - 1][0].mean(dim=0).detach().numpy()

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=["Layer 0 (Early)", f"Layer {n_layers - 1} (Late)"],
        horizontal_spacing=0.12,
    )

    for col, attn in enumerate([early_attn, late_attn], start=1):
        fig.add_trace(
            go.Heatmap(
                z=attn.tolist(),
                x=token_list,
                y=token_list,
                colorscale="Blues",
                showscale=col == 2,  # noqa: PLR2004 - second subplot
                hovertemplate=("From: %{y}<br>To: %{x}<br>Weight: %{z:.3f}<extra></extra>"),
            ),
            row=1,
            col=col,
        )

    fig.update_layout(
        title="Attention Patterns: Early vs Late Layer",
        width=950,
        height=500,
        template="plotly_white",
    )
    return fig.to_html(full_html=False, include_plotlyjs=PLOTLY_JS)


def plot_layer_flow(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequence: str | None = None,
    target_position: int = -1,
) -> str:
    """Show how attention builds up across layers for a target token.

    For a single target token position, shows which source tokens it
    attends to at each layer (averaged across heads).

    Args:
        model: GPT-2 model.
        tokenizer: The tokenizer.
        sequence: Input token sequence. If None, uses a default example.
        target_position: Which token to analyze (-1 = last token).

    Returns:
        HTML string containing the interactive plotly chart.
    """
    if sequence is None:
        sequence = DEFAULT_SEQUENCE_LONG

    attentions, token_list = _get_attention(model, tokenizer, sequence)
    n_layers = len(attentions)
    seq_len = len(token_list)

    if target_position < 0:
        target_position = seq_len + target_position

    flow = []
    for layer_idx in range(n_layers):
        attn = attentions[layer_idx][0].mean(dim=0).detach().numpy()
        flow.append(attn[target_position, :].tolist())

    target_name = token_list[target_position]
    layer_labels = [f"Layer {i}" for i in range(n_layers)]

    fig = go.Figure(
        data=go.Heatmap(
            z=flow,
            x=token_list,
            y=layer_labels,
            colorscale="Blues",
            hovertemplate=("Source: %{x}<br>%{y}<br>Weight: %{z:.3f}<extra></extra>"),
        ),
    )
    fig.update_layout(
        title=f'Attention flow to "{target_name}" (position {target_position})',
        width=950,
        height=350,
        template="plotly_white",
        xaxis={"side": "bottom"},
    )
    return fig.to_html(full_html=False, include_plotlyjs=PLOTLY_JS)


def plot_early_vs_late_attention(
    model: GPT2LMHeadModel,
    tokenizer: PreTrainedTokenizerFast,
    sequence: str | None = None,
    target_position: int = -1,
) -> str:
    """Compare attention patterns between the first and last layer.

    Shows two horizontal bar charts side by side: where the target token
    attends in layer 0 vs the last layer.

    Args:
        model: GPT-2 model loaded with ``attn_implementation='eager'``.
        tokenizer: The tokenizer.
        sequence: Input token sequence. If None, uses a default example.
        target_position: Which token to analyze (-1 = last token).

    Returns:
        HTML string containing the interactive plotly chart.
    """
    if sequence is None:
        sequence = DEFAULT_SEQUENCE_LONG

    attentions, token_list = _get_attention(model, tokenizer, sequence)
    n_layers = len(attentions)
    seq_len = len(token_list)

    if target_position < 0:
        target_position = seq_len + target_position

    colors = [TOKEN_COLORS[categorize_token(t)] for t in token_list]
    target_name = token_list[target_position]

    early_attn = attentions[0][0].mean(dim=0).detach().numpy()[target_position]
    late_attn = attentions[n_layers - 1][0].mean(dim=0).detach().numpy()[target_position]

    top_early = token_list[early_attn.argmax()]
    top_late = token_list[late_attn.argmax()]

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=[
            f"Layer 0 (Early) — top: {top_early} ({early_attn.max():.0%})",
            f"Layer {n_layers - 1} (Late) — top: {top_late} ({late_attn.max():.0%})",
        ],
        horizontal_spacing=0.15,
    )

    for col, attn in enumerate([early_attn, late_attn], start=1):
        fig.add_trace(
            go.Bar(
                x=attn.tolist()[::-1],
                y=token_list[::-1],
                orientation="h",
                marker_color=colors[::-1],
                showlegend=False,
                hovertemplate="%{y}: %{x:.1%}<extra></extra>",
            ),
            row=1,
            col=col,
        )

    fig.update_layout(
        title=f'Attention from "{target_name}": Early vs Late Layer',
        width=950,
        height=450,
        template="plotly_white",
    )
    return fig.to_html(full_html=False, include_plotlyjs=PLOTLY_JS)
