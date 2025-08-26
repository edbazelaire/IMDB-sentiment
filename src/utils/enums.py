from enum import Enum, auto

class EErrorLevel(Enum):
    NONE    = auto()
    WARNING = auto()
    ERROR   = auto()
    FATAL   = auto()

class EModelType(Enum):
    BASELINE    = "baseline"
    LORA        = "lora"