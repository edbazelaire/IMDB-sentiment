import os
import json
import yaml
from pathlib import Path
from typing import Union
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import joblib
import torch

# -- internal
from src.utils.ErrorHandler import ErrorHandler
from src.utils.enums import EModelType


class FileManager:
    # -- reports
    REPORTS_DIR:                str = "reports"
    LIME_HTML_FILE:             str = "lime_explanation.html"
    ATTENTION_HTML_FILE:        str = "attention.html"
    # -- results
    RESULTS_DIR:                str = "results"
    # -- artifacts 
    ARTIFACTS_DIR:              str = "artifacts"
    TRAINING_OUTPUT_DIR:        str = "training_output"
    # -- configs
    CONFIGS_DIR :               str = "configs"
    # -- default values
    DEFAULT_MODEL_NAME :        str = "model"

    _root: str = "";
    _model_id: str = ""
    
    # ===============================================================================================
    # GENERAL METHODS
    @staticmethod
    def init(model_id: str):
        FileManager.init_root()
        
        # TODO : check file id is conform (no forbidden characters)
        FileManager._model_id = model_id
        
    @staticmethod
    def get_root():
        if not FileManager._root:
            FileManager.init_root()    
        return FileManager._root
        
    @staticmethod
    def init_root():
        FileManager._root = Path(__file__).resolve().parents[2];      

    @staticmethod
    def get_model_id():
        return FileManager._model_id

    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> Path:
        """
        Ensure that a directory exists. Create it if missing.
        """
        p = Path(path)

        # If path points to a file (e.g., has suffix), take its parent
        if p.suffix:  
            p = p.parent

        # Only mkdir if it's really a directory
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        elif not p.is_dir():
            raise FileExistsError(f"Path exists and is not a directory: {p}")

        return p

    @staticmethod
    def ensure_file(path: Union[str, Path], create_empty: bool = True) -> Path:
        """
        Ensure that a file exists. Create it if missing.

        Args:
            path (str | Path): File path.
            create_empty (bool): If True, creates an empty file when it doesn't exist.

        Returns:
            Path: The file path as a Path object.
        """
        p = Path(path)
        if not p.exists() and create_empty:
            FileManager.ensure_dir(p.parent)
            p.touch()
        return p

    @staticmethod
    def write(path: Union[str, Path], content: str, append: bool = False):
        """
        Write text content to a file.

        Args:
            path (str | Path): File path.
            content (str): Text to write.
            append (bool): If True, append instead of overwrite.
        """
        FileManager.ensure_dir(Path(path).parent)
        mode = "a" if append else "w"
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def write_json(path: Union[str, Path], content: json, indent:int=2):
        """
        Write json content to a json.

        Args:
            path (str | Path):  File path.
            content (json):     json to write.
        """
        FileManager.ensure_dir(Path(path).parent)
        with open(path, "w") as f:
            json.dump(content, f, indent=indent)

    @staticmethod
    def read_text(path: Union[str, Path]) -> str:
        """
        Read text content from a file.

        Args:
            path (str | Path): File path.

        Returns:
            str: File contents (empty string if file does not exist).
        """
        p = Path(path)
        if not p.exists():
            return ""
        with open(p, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def exists(path: Union[str, Path]) -> bool:
        """Check if a file or directory exists."""
        return Path(path).exists()

    @staticmethod
    def delete(path: Union[str, Path]):
        """Delete a file if it exists."""
        p = Path(path)
        if p.exists() and p.is_file():
            p.unlink()

    # ===============================================================================================
    # ERROR LOGS
    @staticmethod
    def create_errorlogs_file():
        """
        Create a new file for the error logs

        Returns:
            str: path to the created file
        """
        logpath = os.path.join(FileManager.get_root(), FileManager.REPORTS_DIR, f"errorlogs_{FileManager.get_model_id()}.log")
        FileManager.ensure_file(logpath)
        return logpath;

    # ===============================================================================================
    # CONFIGS
    @staticmethod
    def load_config(config_path: str = None):
        """
        Load project configuration from a YAML file.

        Args:
            config_path (str, optional) : Path to the YAML config file. If None, defaults to configs/default.yaml at the project root.

        Returns:
            dict: Configuration dictionary.
        """
        if config_path is None:
            config_path = os.path.join(FileManager.get_root(), "configs", "default.yaml")

        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        return cfg

    # ===============================================================================================
    # SAVING / LOADING MODELS
    @staticmethod
    def load_model(model_type: EModelType, model_id: str):
        """ 
        Load the requested model
        
        Args:
            model_type (EModelType) : type of model (lora, baseline, ...)
            model_id (str)          : special unique identifier for the model.

        Returns:
            model loaded and ready to be used
        """
        model_path = FileManager.get_model_path(model_type=model_type, model_id=model_id, must_exist=True);
        if model_type == EModelType.BASELINE:
            return joblib.load(model_path)
        elif model_type == EModelType.LORA:
            model, _ = FileManager.load_lora(model_id)
            return model
        else:
            ErrorHandler.fatal("Unhandled case : " + model_type)
      
    @staticmethod
    def load_lora(model_id: str, allow_gpu: bool = True):
        """
        Load a lora model from its id (+ the tokenizer) already setup from configs
        
        Args:
            model_id (str)          : special unique identifier for the model.

        Returns:
            model loaded and ready to be used
            tokenizer
        """
         # get path to the model (fatal error if not existing)
        model_path = FileManager.get_model_path(model_type=EModelType.LORA, model_id=model_id, must_exist=True);
        
        # load tokenizer and model from the config files
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        
        # setup model to GPU if possible
        device = torch.device("cuda" if allow_gpu and torch.cuda.is_available() else "cpu")
        model = model.to(device)    # use gpu (if possible) to run the predictions
        model.eval()                # put model in eval mode (small speed boost)
        
        return model, tokenizer

    @staticmethod
    def get_models_save_dirpath(model_type: EModelType):
        """ 
        Get path to the directory where the artifacts will be saved for this type of model
        
        Args:
            model_type (EModelType) : type of model (lora, baseline, ...)

        Returns:
            str: path to the directory
        """
        return os.path.join(FileManager.get_root(), FileManager.ARTIFACTS_DIR, str(model_type.value))
        
    @staticmethod
    def get_training_output_dirpath(model_type: EModelType, model_name: str = "", model_id: str = ""):
        """ 
        Get path to the directory where the training outputs will be saved for this specific model 
        
        Args:
            model_type (EModelType) : type of model (lora, baseline, ...)
            model_name (str)        : special name for the model (act like an extra identifier)
            model_id (str)          : special unique identifier for the model.

        Returns:
            str: path to the created directory
        """
        path = os.path.join(FileManager.get_models_save_dirpath(model_type), FileManager.TRAINING_OUTPUT_DIR, f"{model_name}_{FileManager.get_model_id()}")
        FileManager.ensure_dir(path)
        return path;

    @staticmethod
    def get_model_path(model_type: EModelType, model_name: str = "", model_id: str = "", must_exist: bool = False):
        """
        Create a new file for the error logs

        Args:
            model_type (EModelType) : type of model (lora, baseline, ...)
            model_name (str)        : special name for the model (act like an extra identifier)
            model_id (str)          : special unique identifier for the model.
            must_exist (bool)       : throw an error if the file is not found

        Returns:
            str: path to the created directory
        """
        # fit with default values
        if model_name == "":
            model_name = FileManager.DEFAULT_MODEL_NAME
        if model_id == "":
            model_id = FileManager.get_model_id()
        
        # find path (dir or file) depending on model type
        dirpath = FileManager.get_models_save_dirpath(model_type);
        FileManager.ensure_dir(dirpath)
        if model_type == EModelType.BASELINE:
            path = os.path.join(dirpath, f"{model_name}_{model_id}.joblib");  
        elif model_type == EModelType.LORA:
            path = os.path.join(dirpath, f"{model_name}_{model_id}")
            if not must_exist:
                FileManager.ensure_dir(path)
        else:
            ErrorHandler.error("Unhandled case : " + model_type)
            return ""
        
        # check exists (if required)
        if must_exist and not os.path.exists(path):
            ErrorHandler.fatal("Trying to find model id that does not exists : " + path)
            return ""
        
        # return path to the model
        return path;

    @staticmethod
    def check_model_exists(model_type: EModelType, model_name: str = DEFAULT_MODEL_NAME, model_id: str = ""):
        """
        Check that a specific model exists

        Args:
            model_type (EModelType) : type of model (lora, baseline, ...)
            model_id (str)          : special unique identifier for the model.

        Returns:
            str: path to the created directory
        """
        dirpath = FileManager.get_models_save_dirpath(model_type);
        if model_type == EModelType.BASELINE:
            path = os.path.join(dirpath, f"{model_name}_{model_id}.joblib");  
        elif model_type == EModelType.LORA:
            path = os.path.join(dirpath, f"{model_name}_{model_id}")
        else:
            ErrorHandler.error("Unhandled case : " + model_type)
            return False
        
        return os.path.exists(path)

    @staticmethod
    def get_last_model_id(model_type: EModelType, model_name: str = "") -> str:
        """
        Find the most recent model id for a given model type and optional model name.

        Args:
            model_type (EModelType): type of model (lora, baseline, ...)
            model_name (str): optional prefix for the model (default: "model")

        Returns:
            str: The most recent model_id found, or "" if none exists.
        """
        if model_name == "":
            model_name = FileManager.DEFAULT_MODEL_NAME

        dirpath = FileManager.get_models_save_dirpath(model_type)
        if not os.path.exists(dirpath):
            return ""

        # list all files/folders in the directory matching pattern
        items = list(Path(dirpath).glob(f"{model_name}_*"))
        if not items:
            return ""

        # sort by modification time, descending
        items.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        last_item = items[0]

        # extract the model_id from filename (after last "_")
        stem = last_item.stem
        if "_" in stem:
            return stem.split("_")[-1]
        return ""

    # ===============================================================================================
    # RESULTS
    @staticmethod
    def get_model_results_file(model_name: str = "", model_id: str = ""):
        """
        Create a new file for the error logs

        Args:
            model_type (EModelType) : type of model (lora, baseline, ...)
            model_name (str)        : special name for the model (act like an extra identifier)
            model_id (str)          : special unique identifier for the model.

        Returns:
            str: path to the created file
        """
        if model_name == "":
            model_name = FileManager.DEFAULT_MODEL_NAME
        if model_id == "":
            model_id = FileManager.get_model_id()
        
        path = os.path.join(FileManager.get_root(), FileManager.RESULTS_DIR, f"results_{model_name}_{FileManager.get_model_id()}.json")
        FileManager.ensure_file(path)
        return path;

    # ===============================================================================================
    # REPORTS
    @staticmethod
    def get_model_reports_dir(model_name: str = "", model_id: str = "", file_name: str = ""):
        """
        Create a new file for the error logs

        Args:
            model_name (str)        : special name for the model (act like an extra identifier)
            model_id (str)          : special unique identifier for the model.

        Returns:
            str: path to the created file
        """
        if model_name == "":
            model_name = FileManager.DEFAULT_MODEL_NAME
        if model_id == "":
            model_id = FileManager.get_model_id()
        
        path = os.path.join(FileManager.get_root(), FileManager.REPORTS_DIR, f"results_{model_name}_{FileManager.get_model_id()}")
        FileManager.ensure_dir(path)
        return path;

    @staticmethod
    def get_model_reports_file(file_name: str, model_name: str = "", model_id: str = ""):
        """
        Create a new file for the error logs

        Args:
            file_name (str)         : name of the file to get
            model_name (str)        : special name for the model (act like an extra identifier)
            model_id (str)          : special unique identifier for the model.

        Returns:
            str: path to the created file
        """
        if file_name == "":
            ErrorHandler.error("bad file name provided : " + file_name)
            return ""
        
        return os.path.join(FileManager.get_model_reports_dir(model_name, model_id), file_name)

