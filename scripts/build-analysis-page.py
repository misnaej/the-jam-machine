"""Generate the Embedding Explorer HTML page for GitHub Pages.

Runs all analysis visualizations and embeds them in a self-contained
HTML file at docs/exploring_the_embedding.html.

Usage:
    pipenv run python scripts/build-analysis-page.py
"""

from __future__ import annotations

import base64
import logging
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt
from transformers import GPT2Config, GPT2LMHeadModel, PreTrainedTokenizerFast

from jammy.analysis.activation import plot_prediction_comparison, plot_top_predictions
from jammy.analysis.attention import (
    plot_attention_comparison,
    plot_early_vs_late_attention,
    plot_layer_flow,
)
from jammy.analysis.embedding import (
    plot_embedding_comparison,
    plot_embedding_heatmap_comparison,
    plot_tsne,
)
from jammy.analysis.head_roles import (
    analyze_head_roles,
    plot_head_comparison,
)
from jammy.constants import MODEL_REPO, MODEL_REVISION
from jammy.logging_config import setup_logging

logger = logging.getLogger(__name__)

OUTPUT_PATH = Path("docs/exploring_the_embedding.html")

SAMPLE_SEQUENCES = [
    "PIECE_START TRACK_START INST=DRUMS DENSITY=2"
    " BAR_START NOTE_ON=36 TIME_DELTA=2 NOTE_OFF=36 BAR_END",
    "PIECE_START TRACK_START INST=4 DENSITY=3"
    " BAR_START NOTE_ON=40 TIME_DELTA=4 NOTE_OFF=40 BAR_END",
    "PIECE_START TRACK_START INST=3 DENSITY=2"
    " BAR_START NOTE_ON=60 TIME_DELTA=8 NOTE_OFF=60 BAR_END",
    "PIECE_START TRACK_START INST=10 DENSITY=1"
    " BAR_START NOTE_ON=72 TIME_DELTA=16 NOTE_OFF=72 BAR_END",
    "PIECE_START TRACK_START INST=DRUMS DENSITY=3"
    " BAR_START NOTE_ON=42 TIME_DELTA=1 NOTE_OFF=42"
    " NOTE_ON=36 TIME_DELTA=2 NOTE_OFF=36 BAR_END",
]


def _fig_to_base64(fig: plt.Figure) -> str:
    """Convert a matplotlib figure to a base64-encoded PNG string."""
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode("utf-8")


def _img_tag(b64: str, alt: str) -> str:
    """Create an HTML img tag from a base64 string."""
    return (
        f'<img src="data:image/png;base64,{b64}" alt="{alt}"'
        f' style="max-width:100%; margin: 20px 0;">'
    )


def main() -> None:
    """Generate the analysis HTML page."""
    setup_logging(log_to_file=False)

    logger.info("Loading trained model...")
    model = GPT2LMHeadModel.from_pretrained(
        MODEL_REPO,
        revision=MODEL_REVISION,
        attn_implementation="eager",
    )
    tokenizer = PreTrainedTokenizerFast.from_pretrained(MODEL_REPO, revision=MODEL_REVISION)

    logger.info("Creating untrained model...")
    untrained = GPT2LMHeadModel(
        GPT2Config(
            vocab_size=tokenizer.vocab_size,
            pad_token_id=tokenizer.pad_token_id,
            n_embd=512,
            n_head=8,
            n_layer=6,
            n_positions=2048,
        )
    )

    sections = []

    # --- Embedding ---
    logger.info("Generating TSNE...")
    sections.append(
        (
            "Token Embedding Space (TSNE)",
            """
        <p>Each dot is a token from the model's vocabulary (301 tokens total).
        Position is determined by TSNE dimensionality reduction from 512 dimensions to 2.
        Tokens that the model considers similar are placed close together.</p>
        <p><strong>What to look for:</strong> Instruments (blue) cluster tightly — the model
        learned they appear in similar contexts. Time deltas (red) form their own group.
        Notes (black) spread across the space — nearby pitches are somewhat close, but the
        model distinguishes high from low notes.</p>
    """,
            _fig_to_base64(plot_tsne(model, tokenizer)),
        )
    )

    logger.info("Generating TSNE comparison...")
    sections.append(
        (
            "Trained vs Untrained Embedding",
            """
        <p>Left: trained model. Right: untrained model (random weights).
        The trained model organizes tokens into meaningful clusters.
        The untrained model is random noise — no structure at all.</p>
    """,
            _fig_to_base64(plot_embedding_comparison(model, untrained, tokenizer)),
        )
    )

    logger.info("Generating embedding heatmap comparison...")
    sections.append(
        (
            "Embedding Matrix: Trained vs Untrained",
            """
        <p>The raw embedding matrix — each row is a token, each column is one of 512
        embedding dimensions. Tokens are grouped by category (structure, instrument,
        density, notes, time, special). The trained model shows visible patterns within
        categories. The untrained model is uniform noise.</p>
    """,
            _fig_to_base64(plot_embedding_heatmap_comparison(model, untrained, tokenizer)),
        )
    )

    # --- Predictions ---
    logger.info("Generating top predictions...")
    sections.append(
        (
            "Next Token Predictions",
            """
        <p>For each token in a drum sequence, what does the model predict comes next?
        Bars show the top 10 most likely tokens and their probabilities.</p>
        <p><strong>What to look for:</strong> After PIECE_START, the model predicts TRACK_START
        with near certainty. After INST=DRUMS, it predicts DENSITY tokens. After BAR_START,
        it predicts drum notes (NOTE_ON=42, 36, 35). The model has learned the grammar
        of MIDI text.</p>
    """,
            _fig_to_base64(plot_top_predictions(model, tokenizer)),
        )
    )

    logger.info("Generating prediction comparison...")
    sections.append(
        (
            "Predictions: Trained vs Untrained",
            """
        <p>Same sequence, two models. The trained model makes sharp, confident predictions.
        The untrained model spreads probability nearly uniformly — it has no idea what
        should come next.</p>
    """,
            _fig_to_base64(plot_prediction_comparison(model, untrained, tokenizer)),
        )
    )

    # --- Attention ---
    logger.info("Generating attention comparison...")
    sections.append(
        (
            "Attention Patterns: Early vs Late Layer",
            """
        <p>Each cell shows how much one token attends to another (darker = more attention).
        Left: Layer 0 (first layer). Right: Layer 5 (last layer).</p>
        <p><strong>What to look for:</strong> Layer 0 shows a strong diagonal (each token
        attends to itself and nearby tokens). Layer 5 shows vertical dark columns on
        structural tokens (DENSITY, INST) — later tokens look back at these "anchor" tokens
        regardless of distance. This is how the model maintains awareness of context.</p>
    """,
            _fig_to_base64(plot_attention_comparison(model, tokenizer)),
        )
    )

    logger.info("Generating early vs late attention...")
    sections.append(
        (
            "Attention Flow: Early vs Late",
            """
        <p>Where does the last token (BAR_END) look for information? Bar charts show
        attention weights on each source token.</p>
        <p><strong>What to look for:</strong> Early layer spreads attention somewhat evenly.
        Late layer concentrates heavily on specific tokens — the model has learned which
        tokens carry the most useful information for predicting what comes next.</p>
    """,
            _fig_to_base64(plot_early_vs_late_attention(model, tokenizer)),
        )
    )

    logger.info("Generating layer flow...")
    sections.append(
        (
            "Information Flow Across Layers",
            """
        <p>How attention to the last token builds up through all 6 layers. Each row is a layer,
        columns are source tokens, darker = stronger attention weight.</p>
        <p><strong>What to look for:</strong> Attention shifts as you go deeper. Early layers
        may attend to nearby tokens. Middle layers might discover TIME_DELTA patterns.
        The final layer focuses on the tokens most relevant for the next prediction.</p>
    """,
            _fig_to_base64(plot_layer_flow(model, tokenizer)),
        )
    )

    # --- Head Roles ---
    logger.info("Analyzing head roles...")
    roles = analyze_head_roles(model, tokenizer, SAMPLE_SEQUENCES)

    logger.info("Generating head comparison...")
    sections.append(
        (
            "Head Specialization",
            """
        <p>Each of the model's 48 attention heads (6 layers x 8 heads) can specialize in
        tracking different aspects of the music. Here we show the two heads with the most
        different attention profiles — one might focus almost entirely on structure tokens,
        while another distributes attention across instruments and density.</p>
        <p><strong>What to look for:</strong> The bar lengths show what proportion of
        attention each head pays to each token category. This specialization emerges
        from training — it's not designed in. Different heads learn complementary roles.</p>
    """,
            _fig_to_base64(plot_head_comparison(roles)),
        )
    )

    # --- Build HTML ---
    logger.info("Building HTML...")
    html_sections = []
    for title, description, img_b64 in sections:
        html_sections.append(f"""
        <section>
            <h2>{title}</h2>
            {description}
            {_img_tag(img_b64, title)}
        </section>
        <hr>
        """)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Embedding Explorer — The Jam Machine</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont,
                "Segoe UI", Helvetica, Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #1a1a2e; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }}
        h2 {{ color: #16213e; margin-top: 40px; }}
        p {{ font-size: 15px; }}
        img {{ border: 1px solid #eee; border-radius: 4px; }}
        hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 40px 0; }}
        .intro {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        a {{ color: #2196F3; }}
    </style>
</head>
<body>
    <h1>Exploring the Embedding and Attention</h1>
    <div class="intro">
        <p>This page explores how The Jam Machine's GPT-2 model internally represents
        MIDI music tokens. Through visualizations of the embedding space, attention patterns,
        and head specialization, we can see what the model has learned about musical structure.</p>
        <p>All visualizations are generated from the trained model
        (<code>{MODEL_REPO}</code>) using the
        <a href="https://github.com/misnaej/the-jam-machine/tree/main/src/jammy/analysis"
>jammy.analysis</a> module.</p>
        <p><a href=".">← Back to home</a></p>
    </div>

    {"".join(html_sections)}

    <p style="text-align: center; color: #999; margin-top: 40px;">
        Generated by <code>scripts/build-analysis-page.py</code>
    </p>
</body>
</html>"""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html)
    logger.info("Written to %s", OUTPUT_PATH)


if __name__ == "__main__":
    main()
