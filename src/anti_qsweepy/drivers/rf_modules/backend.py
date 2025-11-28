from enum import Enum, auto
from abc import abstractmethod

class BACKENDS(Enum):
    WAVESHARE_USB_CAN_A = auto()
    PYTHON_CAN_GS_USB = auto()

class Backend:
    def __init__(self, addr:str):
        self.addr:str = addr
        self.type:BACKENDS|None = None

    @abstractmethod
    def close(self)->None:
        pass

    @abstractmethod
    def send(self, can_id:int, data:bytes) -> None:
        pass

    @abstractmethod
    def receive(self) -> tuple[int, bytes] | tuple[None, None]:
        pass
