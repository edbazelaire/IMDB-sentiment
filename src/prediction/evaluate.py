import argparse
import numpy as np
from re import I
from sklearn.metrics import classification_report

# -- internal
from src.utils.ErrorHandler import ErrorHandler
from src.utils.FileManager import FileManager
from src.utils.enums import EModelType
from src.utils.utils import LABELS, init_model_id_context
from src.utils.prediction_methods import delegate_predict_fn
from src.data.data import load_imdb


def evaluate(model_type: EModelType, model_id: str, batch_size:int=32, npreds:int=None):
    """
    Evaluate the fine-tuned LoRA transformer model on the IMDB test set.
        - Loads the tokenizer and model from artifacts,
        - Runs predictions on the test split in batches
        - Prints a classification report.

    Args:
        model_id (str)          : id of the model used for evaluation (default : get last LORA model)
        model_type  (EModelType): Type of model to use ("baseline" or "lora").
        batch_size (int)        : size of the batch
        npreds (int, optional)  : max number of predictions (all provided data if is None)
    Returns:
        None 
    """ 
    # initialize context
    init_model_id_context(model_type=model_type, model_id=model_id, use_last_model_id=True)

    # load test data
    _, test_df = load_imdb()
    
    # adjuste size of predictions
    if npreds is not None and npreds > 0:
        test_df = test_df.sample(n=npreds)
    texts = test_df["text"].tolist();

    # get the prediction method that works for the requested model
    predict_fn = delegate_predict_fn(model_type=model_type, model_id=FileManager.get_model_id())    
    preds = predict_fn(texts)           # batch predict the test data     
    preds = np.argmax(preds, axis=1)    # take the class with highest prob

    # display predictions to the console
    print(classification_report(test_df["label"], preds, target_names=LABELS))
    

def main():
    ap = argparse.ArgumentParser("Evaluate a model on the test dataset to see how it performs. Print to the console accuracy metrics (f1 score, accuracy, recall, precision, ...)")
    ap.add_argument("--model_type", type=EModelType, choices=list(EModelType), default=EModelType.LORA, help=f"Type of model you want to use for the prediction : {[e.value for e in EModelType]}")
    ap.add_argument("--model_id",   type=str,               help="Unique identifier for this model that you want to use in the prediction (default: use latest model).")    
    ap.add_argument("--batch_size", type=int, default=32,   help="Size of prediction batches (default = 32)")    
    ap.add_argument("--npreds",     type=int, default=None, help="Limit number of predictions - it will select n random values in the test dataset. (default : use the entire test set)")
    args = ap.parse_args()
    
    evaluate(model_type=args.model_type, model_id=args.model_id, batch_size=args.batch_size, npreds=args.npreds)


if __name__ == "__main__":
    main()