from __future__ import annotations

import logging
from pathlib import Path

import torch
from transformers import GPT2LMHeadModel, PreTrainedTokenizerFast

logger = logging.getLogger(__name__)


class LoadModel:
    """Load GPT-2 model and tokenizer from HuggingFace or local path.

    Example:
        # Load from HuggingFace
        model_repo = "misnaej/the-jam-machine"
        model, tokenizer = LoadModel(
            model_repo, from_huggingface=True
        ).load_model_and_tokenizer()

        # Load from local folder
        model_path = "models/model_2048_wholedataset"
        model, tokenizer = LoadModel(
            model_path, from_huggingface=False
        ).load_model_and_tokenizer()
    """

    def __init__(
        self,
        path: str,
        from_huggingface: bool = True,
        device: str = "cpu",
        revision: str | None = None,
    ) -> None:
        """Initialize the model loader.

        Args:
            path: HuggingFace repo ID or local path to model.
            from_huggingface: Whether to load from HuggingFace Hub.
            device: Device to load model on ('cpu' or 'cuda').
            revision: Specific model revision/commit to load.

        Raises:
            FileNotFoundError: If local path does not exist.
        """
        if not from_huggingface and not Path(path).exists():
            logger.error("Model path does not exist: %s", path)
            raise FileNotFoundError(f"Model path does not exist: {path}")

        self.from_huggingface = from_huggingface
        self.path = path
        self.device = device
        self.revision = revision
        if torch.cuda.is_available():
            self.device = "cuda"

    def load_model_and_tokenizer(self) -> tuple[GPT2LMHeadModel, PreTrainedTokenizerFast]:
        """Load both model and tokenizer.

        Returns:
            Tuple of (model, tokenizer).
        """
        model = self.load_model()
        tokenizer = self.load_tokenizer()
        return model, tokenizer

    def load_model(self) -> GPT2LMHeadModel:
        """Load the GPT-2 model.

        Returns:
            The loaded GPT-2 language model.
        """
        if self.revision is None:
            model = GPT2LMHeadModel.from_pretrained(self.path)
        else:
            model = GPT2LMHeadModel.from_pretrained(self.path, revision=self.revision)
        return model

    def load_tokenizer(self) -> PreTrainedTokenizerFast:
        """Load the tokenizer.

        Returns:
            The loaded tokenizer.

        Raises:
            FileNotFoundError: If tokenizer.json not found in local path.
        """
        if not self.from_huggingface:
            tokenizer_path = Path(self.path) / "tokenizer.json"
            if not tokenizer_path.exists():
                raise FileNotFoundError(
                    f"No 'tokenizer.json' file in {self.path}"
                )
        tokenizer = PreTrainedTokenizerFast.from_pretrained(self.path)
        return tokenizer
