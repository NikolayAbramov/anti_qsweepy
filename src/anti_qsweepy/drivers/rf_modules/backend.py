from enum import Enum, auto

class BACKENDS(Enum):
    WAVESHARE_USB_CAN_A = auto()
    PYTHON_CAN_GS_USB = auto()

class Backend:
    def __init__(self, addr:str):
        self.addr:str = addr
        self.type:BACKENDS|None = None
