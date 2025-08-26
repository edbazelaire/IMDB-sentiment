import os
from pathlib import Path
from datetime import datetime
from tkinter import E
from loguru import logger

# -- internal
from src.utils.enums import EErrorLevel


class ErrorHandler:
    _initialized:    bool        = False
    
    @staticmethod
    def init(model_id: str):
        dirpath = os.path.join("reports", "errorlogs");
        p = Path(dirpath)
        p.mkdir(parents=True, exist_ok=True)
        logger.add(os.path.join(dirpath,  f"errorlogs_{model_id}.log"), rotation="1 MB", encoding="utf-8", enqueue=True)
        ErrorHandler._initialized = True

    @staticmethod
    def log(message: str, level: EErrorLevel = EErrorLevel.NONE, exception: Exception = None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if level == EErrorLevel.NONE:
            logger.info(f"[{timestamp}] {message}")
        elif level == EErrorLevel.WARNING:
            logger.warning(f"[{timestamp}] {message}")
        elif level == EErrorLevel.ERROR:
            logger.error(f"[{timestamp}] {message} {exception or ''}")
        elif level == EErrorLevel.FATAL:
            logger.critical(f"[{timestamp}] {message} {exception or ''}")
            raise SystemExit(1)

    @staticmethod
    def warning(message: str, exception: Exception = None):
        return ErrorHandler.log(message, EErrorLevel.WARNING, exception)
    
    @staticmethod
    def error(message: str, exception: Exception = None):
        return ErrorHandler.log(message, EErrorLevel.ERROR, exception)
    
    @staticmethod
    def fatal(message: str, exception: Exception = None):
        return ErrorHandler.log(message, EErrorLevel.FATAL, exception)