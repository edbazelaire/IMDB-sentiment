import argparse
import json
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, classification_report
from transformers.trainer import TRAINER_STATE_NAME
from datetime import datetime

# -- internal
from src.data.data import load_imdb
from src.utils.FileManager import FileManager
from src.utils.enums import EModelType
from src.utils.prediction_methods import build_vectorizer
from src.utils.ErrorHandler import ErrorHandler
from src.utils.utils import set_seed, LABELS


def train_baseline(model_id: str):
    FileManager.init(model_id)
    ErrorHandler.init(model_id)
    
    # loading config and setting seed
    cfg = FileManager.load_config();
    set_seed(cfg["seed"])
    
    # loading train/test datasets
    train, test = load_imdb()
    
    # setup pipeline (vectorization + LogReg)  
    pipe = Pipeline([
        ("tfidf", build_vectorizer()),
        ("clf", LogisticRegression(max_iter=cfg["baseline"]["max_iter"], C=cfg["baseline"]["C"], n_jobs=None)),
    ])
    
    # traning the baseline
    ErrorHandler.log("Training baseline TF‑IDF + LogReg…")    
    pipe.fit(train["text"], train["label"])
    
    # make predictions on the "test" data and analyse the results
    preds = pipe.predict(test["text"]) 
    acc = accuracy_score(test["label"], preds)
    f1 = f1_score(test["label"], preds)
    
    # display predictions to the console
    ErrorHandler.log(f"Baseline accuracy={acc:.4f} f1={f1:.4f}")
    ErrorHandler.log("\n"+classification_report(test["label"], preds, target_names=LABELS))

    # save the results in the "reports/" file
    FileManager.write_json(FileManager.get_model_results_file(), {"accuracy": acc, "f1": f1})

    # save model
    joblib.dump(pipe, FileManager.get_model_path(EModelType.BASELINE))
    

def main():
    # setup training argumentes
    ap = argparse.ArgumentParser("Train a baseline TF‑IDF + LogReg model on the IMDB dataset")
    ap.add_argument("--model_id",       type=str,   default=str(int(datetime.now().timestamp() * 1e6)), help="Unique identifier for this model (default: current timestamp).")
    args = ap.parse_args()
    
    train_baseline(args.model_id)

if __name__ == "__main__":
    main()

