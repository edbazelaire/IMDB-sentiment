from fastapi import FastAPI
from pydantic import BaseModel, Field, validator
import torch
import uvicorn

# -- internal
from src.utils.utils import LABELS, LABEL_NEGATIVE, LABEL_POSITIVE
from src.utils.FileManager import FileManager
from src.utils.enums import EModelType

app = FastAPI(title="IMDB Sentiment API")

class Inp(BaseModel):
    text:       str
    model_id:   str = Field(default="latest", description="Model identifier (or 'latest' for most recent model)")
    
    @validator("model_id", pre=True, always=True)
    def validate_model_id(cls, v):
        """Make sure that the 'model_id' parameter is valid"""
        # default value - take latest model existing
        if not v or v == "latest":
            v = FileManager.get_last_model_id(EModelType.LORA)
        
        # check if model exists
        if not FileManager.check_model_exists(model_type=EModelType.LORA, model_id=v):
            raise ValueError(f"Model id '{v}' does not exist")
        
        return v
    

def predict_probs(text, model, tokenizer):
    """
    Use a specific model and tokenizer to predict the probablility for the 
    provided text to be positive or negative
    
    Args:
        text (str)  : text to analyse
        model       : model (lora) used of the prediction
        tokenizer   : tokenizer of the model used to convert text into tokens
        
    Returns:   
        list[float] : for each label, probability that the label is the right label
    """
    t = tokenizer(text, return_tensors="pt", truncation=True)
    with torch.no_grad():
        logits = model(**t).logits
    return torch.softmax(logits, dim=-1).squeeze().tolist()


@app.post("/predict")
async def predict(inp: Inp):
    model, tokenizer = FileManager.load_lora(model_id=inp.model_id, allow_gpu=False)
    probs = predict_probs(inp.text, model, tokenizer)
    label = LABELS[max(range(len(probs)), key=lambda i: probs[i])]
    return {"label": label, "probs": {LABEL_NEGATIVE: probs[0], LABEL_POSITIVE: probs[1]}}


def main():
    uvicorn.run("app.fastapi_app:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
