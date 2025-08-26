import argparse
import json
import numpy as np
import datasets as ds
import pandas as pd
from transformers import (AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer)
from peft import LoraConfig, get_peft_model
from sklearn.metrics import accuracy_score, f1_score
from datetime import datetime

# -- internal
from src.data.data import prepare_dataset
from src.utils.enums import EModelType
from src.utils.utils import init_model_id_context, set_seed
from src.utils.FileManager import FileManager
from src.utils.ErrorHandler import ErrorHandler


def train_lora(model_id: str = "", epochs=2, batch_size=16, max_length=256, lr=2e-5, weight_decay=0.01, warmup_ratio=0.1):
    # initialize context (logging, files, ...)
    init_model_id_context(EModelType.LORA, model_id)
    
    # load configs and use setup model_name
    cfg = FileManager.load_config()
    cfg_lora = cfg["lora"]
    set_seed(cfg["seed"])
    model_name = cfg_lora["model_name"]
    
    ErrorHandler.log(f"Starting training for model {model_name} with id {model_id}")

    # setup dataset
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    train_ds, test_ds = prepare_dataset("imdb", tokenizer, max_length);

    # loaf pretrained model and set lables
    base = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)
    peft_conf = LoraConfig(r=cfg_lora["lora_r"], lora_alpha=cfg_lora["lora_alpha"], lora_dropout=cfg_lora["lora_dropout"], target_modules=["q_lin","v_lin"])
    model = get_peft_model(base, peft_conf)

    # setup training arguments
    args = TrainingArguments(
        output_dir                  = FileManager.get_training_output_dirpath(model_type=EModelType.LORA),
        logging_dir                 = FileManager.get_training_output_dirpath(model_type=EModelType.LORA),
        learning_rate               = lr,                           
        per_device_train_batch_size = batch_size,                       # Batch size per device (GPU/CPU)
        per_device_eval_batch_size  = batch_size,                       # Evaluation batch size per device (GPU/CPU)
        num_train_epochs            = epochs,                           # Number of training epochs
        weight_decay                = weight_decay,                     # Weight decay for regularization
        eval_strategy               = "epoch",                          # Evaluate at each epoch
        save_strategy               = "epoch",                          # Save at each epoch
        logging_steps               = 50,                               # Interval for logging updates
        load_best_model_at_end      = True,                             # Load the best model based on accuracy
        report_to                   = "none",                           # Disable reporting to Hugging Face Hub
        push_to_hub                 = False,                            # Do not push to Hugging Face Hub
        fp16                        = True                              # Enable mixed precision
    )

    # setup Trainer that will retrain the base model
    trainer = Trainer(
        model           = model, 
        args            = args, 
        train_dataset   = train_ds, 
        eval_dataset    = test_ds,
        tokenizer       = tokenizer, 
        compute_metrics = compute_metrics
    )
    
    # start the traning
    trainer.train()
    
    # evaluate the models performance and save in a json local file
    FileManager.write_json(FileManager.get_model_results_file(), trainer.evaluate())

    # save the model with all the related config
    model_path = FileManager.get_model_path(EModelType.LORA)
    model = model.merge_and_unload()      # merge LoRA weights into DistilBERT
    model.save_pretrained(model_path)     # now it’s a full Hugging Face model
    tokenizer.save_pretrained(model_path)


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {"accuracy": accuracy_score(labels, preds), "f1": f1_score(labels, preds)}


def main():
    # load configuration from config file (configs/default.yaml)
    cfg = FileManager.load_config()
    cfg_lora = cfg["lora"]

    # setup training argumentes
    ap = argparse.ArgumentParser(description="Train a LoRA fine-tuned DistilBERT model on the IMDB dataset. The training arguments can be found in the config file : configs/default.yaml")
    ap.add_argument("--epochs",         type=int,   default=cfg_lora["epochs"],         help="Number of training epochs.")
    ap.add_argument("--batch_size",     type=int,   default=cfg_lora["batch_size"],     help="Batch size per device for training and evaluation.")
    ap.add_argument("--max_length",     type=int,   default=cfg_lora["max_length"],     help="Maximum sequence length for tokenization.")
    ap.add_argument("--lr",             type=float, default=cfg_lora["lr"],             help="Learning rate for the AdamW optimizer.")
    
    ap.add_argument("--model_id",       type=str,   default=str(int(datetime.now().timestamp() * 1e6)), help="Unique identifier for this model (default: current timestamp).")
    args = ap.parse_args()
    
    # start training
    train_lora(model_id=args.model_id, epochs=args.epochs, batch_size=args.batch_size, max_length=args.max_length, lr=args.lr)


if __name__ == "__main__":
    main()