"""Model and tokenizer loading from HuggingFace or local path."""

from __future__ import annotations

import logging
from pathlib import Path

import torch
from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast

logger = logging.getLogger(__name__)


def load_model_and_tokenizer(
    path: str,
    *,
    from_huggingface: bool = True,
    revision: str | None = None,
) -> tuple[GPT2LMHeadModel, PreTrainedTokenizerFast]:
    """Load GPT-2 model and tokenizer from HuggingFace or local path.

    Args:
        path: HuggingFace repo ID or local path to model.
        from_huggingface: Whether to load from HuggingFace Hub.
        revision: Specific model revision/commit to load.

    Returns:
        Tuple of (model, tokenizer).

    Raises:
        FileNotFoundError: If local path does not exist or tokenizer.json is missing.

    Example:
        >>> model, tokenizer = load_model_and_tokenizer(
        ...     "JammyMachina/elec-gmusic-familized-model-13-12__17-35-53",
        ...     from_huggingface=True,
        ...     revision="95b3c0905f6a97fdc147776a5b53edaf651916e4",
        ... )
    """
    if not from_huggingface and not Path(path).exists():
        msg = f"Model path does not exist: {path}"
        logger.error(msg)
        raise FileNotFoundError(msg)

    if not from_huggingface:
        tokenizer_path = Path(path) / "tokenizer.json"
        if not tokenizer_path.exists():
            msg = f"No 'tokenizer.json' file in {path}"
            raise FileNotFoundError(msg)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info("Loading model from %s (device=%s, revision=%s)", path, device, revision)

    model = GPT2LMHeadModel.from_pretrained(path, revision=revision)
    tokenizer = PreTrainedTokenizerFast.from_pretrained(path, revision=revision)

    return model, tokenizer
