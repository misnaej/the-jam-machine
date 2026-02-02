"""Low-level GPT-2 model interaction for music generation."""

import logging
from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from transformers import GPT2LMHeadModel, GPT2Tokenizer

logger = logging.getLogger(__name__)


class GenerationEngine:
    """Handles low-level GPT-2 model interaction for tokenization and generation.

    This class encapsulates the core model operations: tokenizing input prompts,
    generating token sequences, and decoding back to text.

    Attributes:
        model: The GPT-2 language model for generation.
        tokenizer: The tokenizer for encoding/decoding text.
        device: The device to run the model on (cpu/cuda).
        max_length: Maximum sequence length from model config.
        no_repeat_ngram_size: N-gram size for repetition penalty.
        generate_until: Token that signals end of generation.
    """

    def __init__(
        self,
        model: "GPT2LMHeadModel",
        tokenizer: "GPT2Tokenizer",
        device: str = "cpu",
    ) -> None:
        """Initialize the generation engine.

        Args:
            model: The GPT-2 language model.
            tokenizer: The tokenizer for the model.
            device: Device to run the model on.
        """
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.max_length = model.config.n_positions
        self.no_repeat_ngram_size = 0
        self.generate_until = "TRACK_END"
        logger.info("Attention length set to %d -> 'model.config.n_positions'", self.max_length)

    def tokenize(self, prompt: str, verbose: bool = True) -> torch.Tensor:
        """Tokenize an input prompt.

        Args:
            prompt: The text prompt to tokenize.
            verbose: Whether to log status messages.

        Returns:
            Tokenized prompt as a tensor.
        """
        if verbose:
            logger.info("Tokenizing input_prompt...")
        return self.tokenizer.encode(prompt, return_tensors="pt")

    def generate_ids(
        self,
        input_ids: torch.Tensor,
        temperature: float,
        verbose: bool = True,
    ) -> torch.Tensor:
        """Generate a sequence of token IDs from input IDs.

        Args:
            input_ids: Tokenized input prompt.
            temperature: Sampling temperature (higher = more random).
            verbose: Whether to log status messages.

        Returns:
            Generated token IDs as a tensor.
        """
        generated_ids = self.model.generate(
            input_ids,
            max_length=self.max_length,
            do_sample=True,
            temperature=temperature,
            no_repeat_ngram_size=self.no_repeat_ngram_size,
            eos_token_id=self.tokenizer.encode(self.generate_until)[0],
        )

        if verbose:
            logger.info("Generating a token_id sequence...")

        return generated_ids

    def decode(self, token_ids: torch.Tensor, verbose: bool = True) -> str:
        """Convert token IDs back to text.

        Args:
            token_ids: Generated token IDs.
            verbose: Whether to log status messages.

        Returns:
            Decoded text string.
        """
        generated_text = self.tokenizer.decode(token_ids[0])
        if verbose:
            logger.info("Converting token sequence to MidiText...")
        return generated_text

    def generate(
        self,
        prompt: str,
        temperature: float,
        verbose: bool = True,
    ) -> str:
        """Full generation pipeline: tokenize -> generate -> decode.

        Args:
            prompt: The text prompt to generate from.
            temperature: Sampling temperature.
            verbose: Whether to log status messages.

        Returns:
            Generated text including the original prompt.
        """
        input_ids = self.tokenize(prompt, verbose=verbose)
        generated_ids = self.generate_ids(input_ids, temperature, verbose=verbose)
        return self.decode(generated_ids, verbose=verbose)

    def set_improvisation_level(self, level: int) -> None:
        """Set the n-gram repetition penalty level.

        Args:
            level: N-gram size for repetition penalty (0 = no penalty).
        """
        self.no_repeat_ngram_size = level
        logger.info("no_repeat_ngram_size set to %d", level)
