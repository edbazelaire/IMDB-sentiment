from pathlib import Path
import random, os, numpy as np, torch
from src.utils.ErrorHandler import ErrorHandler

from src.utils.FileManager import FileManager
from src.utils.enums import EModelType

LABEL_NEGATIVE = "neg"
LABEL_POSITIVE = "pos"
LABELS = [LABEL_NEGATIVE, LABEL_POSITIVE]

def set_seed(seed):
    """
    Make sure that every libs are using the same seed.
    
    Args:
        seed (int) : Value of the seed used to reproduce randomness
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def init_model_id_context(model_type: EModelType, model_id: str, use_last_model_id: bool = False):
    """
    Initialize the context for the model id - if no model_id provided, use the 
    
    Args:
        model_type          (EModelType)    : type of model (baseline, lora, ...)
        model_id            (str)           : unique id of the model
        use_last_model_id   (bool)          : if not id provided, use the last model id
    """
    if use_last_model_id and not model_id:
        model_id = FileManager.get_last_model_id(model_type)
    
    ErrorHandler.init(model_id)
    FileManager.init(model_id)