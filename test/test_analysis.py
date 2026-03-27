"""Tests for the analysis module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from jammy.analysis import categorize_token
from jammy.analysis.embedding import _get_embedding, _get_token_list, _sort_by_category

if TYPE_CHECKING:
    from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast


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
