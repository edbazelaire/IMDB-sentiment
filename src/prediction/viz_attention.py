import argparse
from transformers import AutoConfig, AutoTokenizer, AutoModelForSequenceClassification
import torch
# -- internal
from src.utils.FileManager import FileManager
from src.utils.enums import EModelType
from src.utils.utils import init_model_id_context


def attention_rollout(attentions):
    attn = torch.stack(attentions).mean(1)
    eye = torch.eye(attn.size(-1))
    aug = attn + eye
    rollout = aug[0]
    for i in range(1, aug.size(0)):
        rollout = rollout @ aug[i]
    return rollout


def main():
    ap = argparse.ArgumentParser("Visualise the attention of a LoRA model ")
    ap.add_argument("--text",       type=str, required=True, help="Text that you want to see analysed")
    ap.add_argument("--model_id",   type=str, help="Unique identifier for this model that you want to use in the prediction (default: use latest model).")
    args = ap.parse_args()
    
    # init context
    init_model_id_context(EModelType.LORA, args.model_id, use_last_model_id=True)

    # get path to the model (fatal error if not existing)
    model_path = FileManager.get_model_path(model_type=EModelType.LORA, model_id=FileManager.get_model_id(), must_exist=True);
        
    # load tokenizer and model from the config files
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    config = AutoConfig.from_pretrained(model_path, output_attentions=True)
    model = AutoModelForSequenceClassification.from_pretrained(model_path, config=config)
    
    # setup
    tokens = tokenizer(args.text, return_tensors="pt", truncation=True)
    out = model(**tokens, output_attentions=True)
    rollout = attention_rollout(out.attentions)

    idx_to_tok = tokenizer.convert_ids_to_tokens(tokens["input_ids"][0])
    seq_len = len(idx_to_tok)
    scores = rollout[0, 0, :seq_len].detach().cpu().numpy()
    
    # Normalize 0..1
    smin, smax = float(scores.min()), float(scores.max())
    scores = (scores - smin) / (smax - smin + 1e-9)

    # write an html file content
    spans = []
    for t, s in zip(idx_to_tok, scores):
        # scale alpha to max 0.9 for readability
        spans.append(f"<span style='padding:2px 4px;background-color:rgba(255,0,0,{0.9*s:.3f})'>{t}</span>")
    rows = " ".join(spans)
    html = f"""
    <html><body><h3>Attention rollout</h3><p>{rows}</p></body></html>
    """

    # save html file content in reports (of the model)
    report_path = FileManager.get_model_reports_file(file_name=FileManager.ATTENTION_HTML_FILE, model_id=FileManager.get_model_id())
    FileManager.write(report_path, content=html, append=False)

    print("Saved : " + report_path)


if __name__ == "__main__":
    main()