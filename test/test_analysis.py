"""Tests for the analysis module."""

from __future__ import annotations

import pytest
from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast

from jammy.analysis import categorize_token
from jammy.analysis.activation import plot_prediction_comparison, plot_top_predictions
from jammy.analysis.attention import (
    plot_attention_comparison,
    plot_early_vs_late_attention,
    plot_layer_flow,
)
from jammy.analysis.embedding import (
    _get_embedding,
    _get_token_list,
    _sort_by_category,
    plot_embedding_heatmap_comparison,
    plot_tsne,
)
from jammy.analysis.head_roles import analyze_head_roles, plot_head_comparison
from jammy.constants import MODEL_REPO, MODEL_REVISION


@pytest.fixture(scope="module")
def eager_model() -> GPT2LMHeadModel:
    """Load model with eager attention for attention weight extraction."""
    return GPT2LMHeadModel.from_pretrained(
        MODEL_REPO,
        revision=MODEL_REVISION,
        attn_implementation="eager",
    )


class TestCategorizeToken:
    """Tests for categorize_token."""

    def test_categorize_token_structure(self) -> None:
        """Test structure tokens are categorized correctly."""
        assert categorize_token("PIECE_START") == "structure"
        assert categorize_token("TRACK_START") == "structure"
        assert categorize_token("BAR_END") == "structure"

    def test_categorize_token_instrument(self) -> None:
        """Test instrument tokens are categorized correctly."""
        assert categorize_token("INST=DRUMS") == "instrument"
        assert categorize_token("INST=4") == "instrument"

    def test_categorize_token_density(self) -> None:
        """Test density tokens are categorized correctly."""
        assert categorize_token("DENSITY=2") == "density"

    def test_categorize_token_note(self) -> None:
        """Test note tokens are categorized correctly."""
        assert categorize_token("NOTE_ON=60") == "note"
        assert categorize_token("NOTE_OFF=36") == "note"

    def test_categorize_token_time(self) -> None:
        """Test time tokens are categorized correctly."""
        assert categorize_token("TIME_DELTA=4") == "time"

    def test_categorize_token_special(self) -> None:
        """Test special/unknown tokens are categorized correctly."""
        assert categorize_token("[UNK]") == "special"
        assert categorize_token("[PAD]") == "special"


class TestSortByCategory:
    """Tests for _sort_by_category."""

    def test_sort_by_category_groups_correctly(self) -> None:
        """Test that tokens are grouped by category in the defined order."""
        tokens = ["NOTE_ON=60", "PIECE_START", "TIME_DELTA=4", "INST=3", "DENSITY=1"]
        indices, _sorted_tokens, categories = _sort_by_category(tokens)

        # Structure should come first, then instrument, density, note, time
        assert categories[0] == "structure"
        assert categories[-1] == "time"
        assert len(indices) == len(tokens)

    def test_sort_by_category_preserves_all_tokens(self) -> None:
        """Test that no tokens are lost during sorting."""
        tokens = ["A", "B", "C", "NOTE_ON=1", "INST=0"]
        _indices, sorted_tokens, _categories = _sort_by_category(tokens)
        assert set(sorted_tokens) == set(tokens)


class TestGetEmbedding:
    """Tests for _get_embedding."""

    def test_get_embedding_shape(self, model: GPT2LMHeadModel) -> None:
        """Test that embedding has correct shape (vocab_size x embed_dim)."""
        embedding = _get_embedding(model)
        assert embedding.shape[0] == 301  # model vocab size
        assert embedding.shape[1] == 512  # embedding dimension


class TestGetTokenList:
    """Tests for _get_token_list."""

    def test_get_token_list_length(self, tokenizer: PreTrainedTokenizerFast) -> None:
        """Test that token list matches vocab size."""
        tokens = _get_token_list(tokenizer)
        assert len(tokens) == tokenizer.vocab_size


class TestPlotSmoke:
    """Smoke tests verifying all plot functions return valid HTML."""

    def test_plot_tsne(
        self,
        model: GPT2LMHeadModel,
        tokenizer: PreTrainedTokenizerFast,
    ) -> None:
        """Test that plot_tsne returns two HTML strings."""
        trained_html, untrained_html = plot_tsne(model, model, tokenizer)
        assert "<div" in trained_html
        assert "<div" in untrained_html

    def test_plot_embedding_heatmap_comparison(
        self,
        model: GPT2LMHeadModel,
        tokenizer: PreTrainedTokenizerFast,
    ) -> None:
        """Test that embedding heatmap comparison returns two HTML strings."""
        trained_html, untrained_html = plot_embedding_heatmap_comparison(
            model,
            model,
            tokenizer,
        )
        assert "<div" in trained_html
        assert "<div" in untrained_html

    def test_plot_top_predictions(
        self,
        model: GPT2LMHeadModel,
        tokenizer: PreTrainedTokenizerFast,
    ) -> None:
        """Test that top predictions returns HTML."""
        html = plot_top_predictions(model, tokenizer)
        assert "<div" in html

    def test_plot_prediction_comparison(
        self,
        model: GPT2LMHeadModel,
        tokenizer: PreTrainedTokenizerFast,
    ) -> None:
        """Test that prediction comparison returns HTML."""
        html = plot_prediction_comparison(model, model, tokenizer)
        assert "<div" in html

    def test_plot_attention_comparison(
        self,
        eager_model: GPT2LMHeadModel,
        tokenizer: PreTrainedTokenizerFast,
    ) -> None:
        """Test that attention comparison returns HTML."""
        html = plot_attention_comparison(eager_model, tokenizer)
        assert "<div" in html

    def test_plot_early_vs_late_attention(
        self,
        eager_model: GPT2LMHeadModel,
        tokenizer: PreTrainedTokenizerFast,
    ) -> None:
        """Test that early vs late attention returns HTML."""
        html = plot_early_vs_late_attention(eager_model, tokenizer)
        assert "<div" in html

    def test_plot_layer_flow(
        self,
        eager_model: GPT2LMHeadModel,
        tokenizer: PreTrainedTokenizerFast,
    ) -> None:
        """Test that layer flow returns HTML."""
        html = plot_layer_flow(eager_model, tokenizer)
        assert "<div" in html

    def test_analyze_and_plot_head_comparison(
        self,
        eager_model: GPT2LMHeadModel,
        tokenizer: PreTrainedTokenizerFast,
    ) -> None:
        """Test that head analysis and comparison returns HTML."""
        roles = analyze_head_roles(
            eager_model,
            tokenizer,
            ["PIECE_START TRACK_START INST=DRUMS DENSITY=2"],
        )
        assert roles["n_layers"] == 6
        assert roles["n_heads"] == 8
        html = plot_head_comparison(roles)
        assert "<div" in html
