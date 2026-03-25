"""Training pipeline for The Jam Machine GPT-2 model.

Usage:
    HF_READ_TOKEN=... HF_WRITE_TOKEN=... WANDB_API_KEY=... \
        pipenv run python -m jammy.training.trainer
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import wandb
from datasets import load_dataset
from huggingface_hub import HfApi, create_repo
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    GPT2Config,
    GPT2LMHeadModel,
    Trainer,
    TrainingArguments,
)

from jammy.training.trainer_utils import (
    TokenizeDataset,
    get_history,
    plot_history,
    train_tokenizer,
)

logger = logging.getLogger(__name__)

# CONFIG:
DATASET_NAME = "improved_4bars"
HF_DATASET_REPO = f"JammyMachina/{DATASET_NAME}"
HF_DATASET_REVISION = "30d476e0fe81cb982b0b85660b21fdcf788fe56f"
HF_MODEL_REPO = f"{HF_DATASET_REPO}-mdl"
HF_MODEL_REVISION = "27b0db76a0ff95ba299852c19806f1d7387e6149"
MODEL_PATH = f"models/{DATASET_NAME}"
TRAIN_FROM_CHECKPOINT = True
EVAL_STEPS = 1024
TRAIN_EPOCHS = 5
PER_DEVICE_TRAIN_BATCH_SIZE = 7
GRADIENT_ACCUMULATION_STEPS = 1


def main() -> None:
    """Run the full training pipeline."""
    hf_read_token = os.environ.get("HF_READ_TOKEN", "")
    hf_write_token = os.environ.get("HF_WRITE_TOKEN", "")

    if not hf_read_token or not hf_write_token:
        msg = "HF_READ_TOKEN and HF_WRITE_TOKEN environment variables must be set"
        raise OSError(msg)
    if "WANDB_API_KEY" not in os.environ:
        msg = "WANDB_API_KEY environment variable must be set"
        raise OSError(msg)

    Path(MODEL_PATH).mkdir(parents=True, exist_ok=True)

    wandb.init(project="the-jammy-machine")
    create_repo(HF_MODEL_REPO, token=hf_write_token, exist_ok=True)

    data = load_dataset(
        HF_DATASET_REPO,
        data_files={"train": "train/*.zip", "eval": "validate/*.zip"},
        use_auth_token=hf_read_token,
        revision=HF_DATASET_REVISION,
    )

    if TRAIN_FROM_CHECKPOINT:
        tokenizer = AutoTokenizer.from_pretrained(
            HF_MODEL_REPO,
            use_auth_token=hf_read_token,
            revision=HF_MODEL_REVISION,
        )
    else:
        tokenizer = train_tokenizer(MODEL_PATH, data["train"])

    logger.info("Tokenizing dataset")
    data_tokenized = TokenizeDataset(tokenizer).batch_tokenization(data)

    if TRAIN_FROM_CHECKPOINT:
        model = AutoModelForCausalLM.from_pretrained(
            HF_MODEL_REPO,
            use_auth_token=hf_read_token,
            revision="d1262472162d86c420ed8bf6a8e54270a6186993",
        )
    else:
        model = GPT2LMHeadModel(
            GPT2Config(
                vocab_size=tokenizer.vocab_size,
                pad_token_id=tokenizer.pad_token_id,
                n_embd=512,
                n_head=8,
                n_layer=6,
                n_positions=2048,
            ),
        )

    training_args = TrainingArguments(
        output_dir=MODEL_PATH,
        overwrite_output_dir=True,
        num_train_epochs=TRAIN_EPOCHS,
        evaluation_strategy="steps",
        eval_steps=EVAL_STEPS,
        learning_rate=5e-5,
        per_device_train_batch_size=PER_DEVICE_TRAIN_BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        fp16=True,
        save_strategy="steps",
        save_steps=EVAL_STEPS * 4,
        save_total_limit=5,
        logging_steps=EVAL_STEPS,
        logging_dir=str(Path(MODEL_PATH) / "logs"),
        report_to="wandb",
        seed=42,
        push_to_hub=True,
        hub_model_id=HF_MODEL_REPO,
        hub_token=hf_write_token,
    )
    data_collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=data_tokenized["train"],
        eval_dataset=data_tokenized["eval"],
    )

    with Path(f"{MODEL_PATH}/training_args.json").open("w") as f:
        f.write(training_args.to_json_string())

    result = trainer.train()
    logger.info("Training finished")
    logger.info(result)

    tokenizer.save_pretrained(MODEL_PATH, push_to_hub=True, use_auth_token=hf_write_token)
    trainer.state.save_to_json(f"{MODEL_PATH}/trainer_state.json")
    model.save_pretrained(MODEL_PATH, push_to_hub=True, use_auth_token=hf_write_token)
    trainer.push_to_hub()
    wandb.finish()

    HfApi().upload_folder(
        folder_path=MODEL_PATH,
        repo_id=HF_MODEL_REPO,
        ignore_patterns=[".git/*", "**/.git/*"],
        token=hf_write_token,
    )

    history = get_history(trainer)
    plot_history(history, MODEL_PATH, HF_MODEL_REPO)


if __name__ == "__main__":
    main()
