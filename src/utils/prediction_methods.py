from sklearn.feature_extraction.text import TfidfVectorizer
import torch
import numpy as np
# -- internal
from src.utils.FileManager import FileManager
from src.utils.ErrorHandler import ErrorHandler
from src.utils.enums import EModelType


def build_vectorizer(max_features=20000, ngram_range=(1,2)):
    return TfidfVectorizer(max_features=max_features, ngram_range=ngram_range, lowercase=True, strip_accents='unicode')


def delegate_predict_fn(model_type: EModelType, model_id: str, batch_size: int=32):
    """
    Create a delegated batch prediction method that can be provided to itterate predictions on a list of data
    The delegate methods expects args :
        texts (list[str] | pd.Series):      Input texts
        
    Args:
        model_type  (EModelType)    : type of the model used for the prediction
        model_id    (str)           : id of the model used for the prediction
        batch_size  (int)           : size of prediction batch
        
    Returns:
        function(str|List[str])
    """
    model = FileManager.load_model(model_type, model_id=model_id);
    
    if model_type == EModelType.BASELINE:
        return lambda _text: predict_proba_baseline(model, _text, batch_size=batch_size)
    
    elif model_type == EModelType.LORA:
        _, tokenizer = FileManager.load_lora(model_id)
        return lambda _text: predict_proba_lora(model, tokenizer, _text, batch_size=batch_size)

    ErrorHandler.error("Unhandled case : " + model_type)


def predict_proba_baseline(model, texts, batch_size: int=32):
    """
    Compute prediction probabilities using a scikit-learn model.

    Args:
        model:                      A scikit-learn model with `predict_proba()` method
        texts (str | list[str]):    Input texts
        batch_size  (int) :         size of prediction batch

    Returns:
        np.ndarray: Array of shape (n_samples, n_classes) with predicted probabilities.
    """
    # simple string -> convert into list of strings
    if isinstance(texts, str):
        texts = [texts]
        
    proba = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        preds = model.predict_proba(batch_texts)   
        proba.extend(preds)
    return np.array(proba)  



def predict_proba_lora(model, tokenizer, texts, batch_size: int=32):
    """
    Compute prediction probabilities using a Hugging Face LoRA fine-tuned model.

    Args:
        model:                      A Hugging Face `AutoModelForSequenceClassification` with LoRA weights.
        tokenizer:                  A Hugging Face tokenizer compatible with the model.
        texts (str | list[str]):    Input texts
        batch_size  (int) :         size of prediction batch

    Returns:
        np.ndarray: Array of shape (n_samples, n_classes) with predicted probabilities.
    """
    
    # simple string -> convert into list of strings
    if isinstance(texts, str):
        texts = [texts]

    # check the device used (cuda if possible otherwise cpu)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    # batch prediction
    probs = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        inputs = tokenizer(batch_texts, padding=True, truncation=True, return_tensors="pt").to(device)
        with torch.no_grad():
            logits = model(**inputs).logits
            batch_probs = torch.softmax(logits, dim=-1).cpu().numpy() 
            probs.extend(batch_probs)
    return np.array(probs)  # shape (n_samples, n_classes)