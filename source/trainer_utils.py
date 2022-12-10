import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path
from datetime import datetime

from transformers import PreTrainedTokenizerFast
from tokenizers import Tokenizer
from tokenizers.models import WordLevel
from tokenizers.pre_tokenizers import WhitespaceSplit
from tokenizers.trainers import WordLevelTrainer


class TokenizeDataset:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def tokenize(self, data):
        return self.tokenizer(
            data["text"],
            truncation=True,
            padding=True,
            max_length=2048,
        )

    def batch_tokenization(self, dataset):
        dataset_tokenized = dataset.map(
            self.tokenize, batched=True, remove_columns=["text"]
        )
        return dataset_tokenized


def train_tokenizer(tokenizer_path, train_data, verbose=True):
    if not os.path.isfile(tokenizer_path):
        tokenizer = Tokenizer(WordLevel(unk_token="[UNK]"))
        tokenizer.pre_tokenizer = WhitespaceSplit()
        tokenizer_trainer = WordLevelTrainer(
            special_tokens=["[UNK]", "[PAD]", "[MASK]"]
        )
        tokenizer.train_from_iterator(train_data["text"], trainer=tokenizer_trainer)
        tokenizer.save(tokenizer_path)

    tokenizer = PreTrainedTokenizerFast(tokenizer_file=tokenizer_path)
    tokenizer.add_special_tokens({"pad_token": "[PAD]"})
    print("Vocabulary size: ", tokenizer.vocab_size)
    if verbose:
        print("Vocabulary:")
        [print(voc) for voc in sorted(tokenizer.vocab.items())]

    return tokenizer


def check_tokenized_data(dataset, tokenized_dataset):
    assert "input_ids" in list(tokenized_dataset[0]), list(tokenized_dataset[0])
    for i, data in enumerate(dataset["text"][:100:20]):
        print("----")
        print(data)
        print(tokenized_dataset[i]["input_ids"])


def set_paths(base_path, model_name, datafolder, model_run_in="local"):
    """Set paths either from Google Drive or locally"""
    # formattedtime = datetime.now().strftime("%d-%m__%H-%M-%S")
    formattedtime = "10-12__23-08-42"
    if model_run_in == "gdrive":
        from google.colab import drive

        drive.mount("/content/gdrive")
        base_path = f"/content/gdrive/MyDrive/{base_path}"
    elif model_run_in == "local":
        pass

    dataset_path = f"{base_path}/{datafolder}"
    model_path = f"{base_path}/{model_name}_{formattedtime}"
    tokenizer_path = f"{model_path}/tokenizer.json"
    if not os.path.exists(model_path):
        print(f"Creating model path: {model_path}")
        os.mkdir(model_path)

    return {
        "tokenizer_path": tokenizer_path,
        "dataset_path": dataset_path,
        "model_path": model_path,
    }


def get_history(trainer):
    history = trainer.state.log_history
    train_history = []
    valid_history = []
    for h in history:
        if len(h.items()) == 4:
            train_history.append([h["epoch"], h["step"], h["loss"], h["learning_rate"]])
        elif len(h.items()) == 6:
            valid_history.append([h["epoch"], h["step"], h["eval_loss"]])

    history = {
        "train_epoch": np.array(train_history).T[0],
        "train_loss": np.array(train_history).T[2],
        "learning_rate": np.array(train_history).T[3],
        "valid_epoch": np.array(valid_history).T[0],
        "valid_loss": np.array(valid_history).T[2],
    }
    return history


def plot_history(history, model_path, hf_repo):
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
