from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import matplotlib.pyplot as plt
import numpy as np
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import WhitespaceSplit
from tokenizers.trainers import WordLevelTrainer
from transformers import PreTrainedTokenizerFast

if TYPE_CHECKING:
    from datasets import Dataset, DatasetDict
    from transformers import Trainer

logger = logging.getLogger(__name__)


class TokenizeDataset:
    """Tokenize datasets for training."""

    def __init__(self, tokenizer: PreTrainedTokenizerFast) -> None:
        """Initialize the tokenizer wrapper.

        Args:
            tokenizer: The tokenizer to use for encoding text.
        """
        self.tokenizer = tokenizer

    def tokenize(self, data: dict[str, Any]) -> dict[str, Any]:
        """Tokenize a batch of text data.

        Args:
            data: Dictionary containing 'text' key with strings to tokenize.

        Returns:
            Dictionary with tokenized data.
        """
        return self.tokenizer(
            data["text"],
            truncation=True,
            padding=True,
            max_length=2048,
        )

    def batch_tokenization(self, dataset: DatasetDict) -> DatasetDict:
        """Tokenize an entire dataset.

        Args:
            dataset: HuggingFace dataset to tokenize.

        Returns:
            Tokenized dataset with 'text' column removed.
        """
        dataset_tokenized = dataset.map(self.tokenize, batched=True, remove_columns=["text"])
        return dataset_tokenized


def train_tokenizer(
    model_path: str, train_data: Dataset, verbose: bool = True
) -> PreTrainedTokenizerFast:
    """Train a word-level tokenizer on the training data.

    Args:
        model_path: Path to save the tokenizer.
        train_data: Training dataset with 'text' column.
        verbose: Whether to print vocabulary.

    Returns:
        The trained tokenizer.
    """
    tokenizer_path = Path(model_path) / "tokenizer.json"
    if not tokenizer_path.is_file():
        tokenizer = Tokenizer(WordLevel(unk_token="[UNK]"))  # noqa: S106
        tokenizer.pre_tokenizer = WhitespaceSplit()
        tokenizer_trainer = WordLevelTrainer(special_tokens=["[UNK]", "[PAD]", "[MASK]"])
        tokenizer.train_from_iterator(train_data["text"], trainer=tokenizer_trainer)
        tokenizer.save(str(tokenizer_path))

    tokenizer = PreTrainedTokenizerFast(tokenizer_file=str(tokenizer_path))
    tokenizer.add_special_tokens({"pad_token": "[PAD]"})
    logger.info("Vocabulary size: %d", tokenizer.vocab_size)
    if verbose:
        logger.info("Vocabulary:")
        for voc in sorted(tokenizer.vocab.items()):
            logger.debug(voc)

    return tokenizer


def check_tokenized_data(
    dataset: Dataset,
    tokenized_dataset: Dataset,
    plot_path: str | Path | None = None,
) -> None:
    """Check tokenized data and optionally plot token distribution.

    Args:
        dataset: Original dataset with 'text' column.
        tokenized_dataset: Tokenized dataset with 'input_ids'.
        plot_path: Path to save distribution plot, or None to skip.
    """
    assert "input_ids" in list(tokenized_dataset[0]), list(tokenized_dataset[0])  # noqa: S101
    for i, data in enumerate(dataset["text"][:100:20]):
        logger.info("----")
        logger.info(data)
        logger.info(tokenized_dataset[i]["input_ids"])

    if plot_path is not None:
        inst_tokens = []
        for data in dataset["text"]:
            inst_tokens += [token.strip("INST=") for token in data.split(" ") if "INST=" in token]
        token_occ = np.array(
            [[token, int(inst_tokens.count(token))] for token in np.unique(inst_tokens)]
        ).T
        sorted_occurences = np.sort(token_occ[1].astype(int))
        sorted_tokens = [token_occ[0][idx] for idx in np.argsort(token_occ[1].astype(int))]
        plt.plot(sorted_occurences, color="Black")
        plt.xticks(ticks=range(len(sorted_tokens)), labels=sorted_tokens, rotation=45)
        plt.title("Distribution of instrument tokens in dataset")
        plt.xlabel("Instrument tokens")
        plt.ylabel("Count")
        plt.savefig(f"{plot_path}/_token_distribution_in_dataset.png")
        plt.show()
        plt.close()


def get_history(trainer: Trainer) -> dict[str, np.ndarray]:
    """Extract training history from a trainer.

    Args:
        trainer: HuggingFace Trainer with completed training.

    Returns:
        Dictionary with train/valid epochs, losses, and learning rates.
    """
    history = trainer.state.log_history
    train_history = []
    valid_history = []
    for h in history:
        if len(h.items()) == 4:
            train_history.append([h["epoch"], h["step"], h["loss"], h["learning_rate"]])
        elif len(h.items()) == 6:
            valid_history.append([h["epoch"], h["step"], h["eval_loss"]])

    return {
        "train_epoch": np.array(train_history).T[0],
        "train_loss": np.array(train_history).T[2],
        "learning_rate": np.array(train_history).T[3],
        "valid_epoch": np.array(valid_history).T[0],
        "valid_loss": np.array(valid_history).T[2],
    }


def plot_history(history: dict[str, np.ndarray], model_path: str, hf_repo: str) -> None:
    """Plot training history and save to file.

    Args:
        history: Dictionary from get_history().
        model_path: Path to save the plot.
        hf_repo: Repository name for the plot title.
    """
    plt.subplots(figsize=(10, 10))
    plt.subplot(211)
    plt.plot(history["train_epoch"], history["learning_rate"], color="black")
    plt.xlabel("epochs")
    plt.ylabel("learning rate")
    plt.title(hf_repo)

    plt.subplot(212)
    plt.plot(
        history["train_epoch"],
        history["train_loss"],
        color="purple",
        label="training loss",
    )
    plt.plot(
        history["valid_epoch"],
        history["valid_loss"],
        color="orange",
        label="validation loss",
    )
    plt.legend()
    plt.xlabel("epochs")
    plt.ylabel("loss")

    plt.savefig(f"{model_path}/training_history.png")
    plt.show()
    plt.close()
