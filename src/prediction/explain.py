import argparse
import torch
import numpy as np
import pathlib
import joblib
from lime.lime_text import LimeTextExplainer
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# -- internal
from src.utils.utils import LABELS, init_model_id_context
from src.utils.prediction_methods import delegate_predict_fn
from src.utils.enums import EModelType
from src.utils.FileManager import FileManager
from src.utils.ErrorHandler import ErrorHandler


def explain(text: str, model_type: EModelType, model_id: str = ""):
    """
    Generate a LIME explanation for a given text using the requested type of model (lora, baseline, ...).
    Provides an the detailed prediction and express how impactfull each words are in the decision.

    Args:
        text        (str):              he input text to explain.
        model_type  (EModelType):       Type of model to use ("baseline" or "lora").
        model_id    (str, optional):    Unique identifier of the model. If empty, the most 
                                        recent model_id for the given type is used.
    Returns:
        None
    """
    init_model_id_context(model_type, model_id, use_last_model_id=True)
    model_id = FileManager.get_model_id()
    
    # console / log feedback
    ErrorHandler.log(f"""
    Starting to explain...
        - text : {text}               
        - model_type : {model_type.value}               
        - model_id : {model_id}               
    """)
    
    # make predicion depending on chosen model
    predict_fn = delegate_predict_fn(model_type=model_type, model_id=model_id)

    # display prediction
    explainer = LimeTextExplainer(class_names=LABELS)
    exp = explainer.explain_instance(text, predict_fn, num_features=10, labels=[0,1])
    
    # save reports in reports data file
    report_path = FileManager.get_model_reports_file(file_name=FileManager.LIME_HTML_FILE, model_id=model_id)
    FileManager.write(report_path, content=exp.as_html(), append=False)
    
    # console / log feedback
    ErrorHandler.log("Saved : " + report_path)


def main():
    ap = argparse.ArgumentParser("Explain a model prediction on a provided text. Save results into an html local file at 'reports/MODEL_FILE'")
    ap.add_argument("--text",       type=str, required=True, 
                    help="Text that you want to see analysed")
    ap.add_argument("--model_type", type=EModelType, choices=list(EModelType), default=EModelType.LORA, 
                    help=f"Type of model you want to use for the prediction : {[e.value for e in EModelType]}")
    ap.add_argument("--model_id",   type=str, 
                    help="Unique identifier for this model that you want to use in the prediction (default: use latest model).")    
    args = ap.parse_args()
    
    explain(text=args.text, model_type=args.model_type, model_id=args.model_id)

    
if __name__ == "__main__":
    main()
