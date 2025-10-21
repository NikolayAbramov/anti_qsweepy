import warnings
import logging
import platformdirs
from enum import Enum, auto

from .backend import BACKENDS, Backend

from .definitions import *
from .exceptions import *
from ... import global_defs

class DEVICE_TYPE(Enum):
    TX = 0
    RX = 1

class Device:
    """ Base class for the CAN modules

    When calling constructor to replace an existing object Please use del to delete it first:

    try:
        del obj
    except:
        pass
    obj  = TX()

    Otherwise, driver will be kept locked and the new object will not work.
    """
    def __init__(self, addr:str |Backend ,
                 backend:BACKENDS = BACKENDS.WAVESHARE_USB_CAN_A, channels:list[int]|int = None,
                 log:bool = True):
        self._addr:str = ""
        self._backend_type: BACKENDS = backend
        self.backend: Backend
        self.timeout: float = 1
        self._n_try: int = 3
        # Active channel
        self._ch = 0
        # Valid channels
        self._channels: list[int] | None = None
        if channels is not None:
            self._channels = [channels]

        if type(addr) is str:
            self._addr:str = addr
            self._open_backend()
        elif Backend in type(addr).__mro__:
            self.addr = addr.addr
            self.backend = addr
            self._backend_type = addr.type
        else:
            raise TypeError

        # Logging
        self._log = log
        self._logger = None
        if self._log:
            app_data_pth = platformdirs.user_data_path(global_defs.project_name, appauthor=False)
            if not app_data_pth.exists():
                app_data_pth.mkdir(parents=True)

            self._logger = logging.getLogger(__name__)
            self._logger.setLevel(logging.INFO)

            handler = logging.FileHandler(app_data_pth / "RF_modules.log", mode='a')
            formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.info("Initialized")

        self._flush_rx_buffer()

    def channel(self, ch:int|None = None)->int:
        """Set active channel"""
        if ch is not None:
            if self._channels is not None:
                if ch in self._channels:
                    self._ch = ch
                else:
                    raise ValueError(f"Channel index {ch} is invalid")
            else:
                self._ch = ch
        return self._ch

    def _open_backend(self):
        if self._backend_type is BACKENDS.WAVESHARE_USB_CAN_A:
           from .waveshare_usb_can_a import WaveshareUSB_CAN_A
           self.backend = WaveshareUSB_CAN_A(self._addr, 2000000, 500000)
        elif self._backend_type is BACKENDS.PYTHON_CAN_GS_USB:
           filters = {"can_id": CAN_RESPONSE_BASE_ID, "can_mask": CAN_RESPONSE_BASE_ID}
           from .python_can_backend import PythonCAN_GS_USB_Backend
           self.backend = PythonCAN_GS_USB_Backend(filters)

    def _flush_rx_buffer(self, module_id: int|None = None, param_id: int|None = None) -> tuple[int,bytes|None]:
        """Flush RX buffer of the adapter and try to find lost message if corresponding parameters of the function are
        provided"""
        msg_flushed = 0
        self.backend.timeout = 0.1
        data_recovered = None
        for _ in range(10000):
            can_id, data = self.backend.receive()
            if can_id is None:
                break
            # Try to find wat we need in a pile of frames
            if module_id is not None and param_id is not None:
                param_id_resp = data[-1] >> 1
                module_id_resp = can_id - CAN_RESPONSE_BASE_ID
                if param_id_resp == param_id and module_id_resp == module_id:
                    data_recovered = data
            else:
                msg_flushed += 1
        self.backend.timeout = self.timeout
        return msg_flushed, data_recovered

    def module_id(self):
        """Identify module by initiating its green LED blinking"""
        self._write(self._ch, TX_PARAM_ID.MODULE_ID)

    def device_type(self)->DEVICE_TYPE:
        """Get module type"""
        return DEVICE_TYPE(self._read(self._ch, TX_PARAM_ID.DEVICE_TYPE, 1))

    def _validate_response(self, module_id: int, param_id: int, can_id_resp: int, data_resp: bytes) -> bytes|None:
        actual_param_id = data_resp[-1] >> 1
        actual_module_id = can_id_resp - CAN_RESPONSE_BASE_ID
        if actual_param_id != param_id or actual_module_id != module_id:
            msg_flushed, data_recovered = self._flush_rx_buffer(module_id, param_id)
            if data_recovered is None:
                if msg_flushed > 0:
                    raise RxBufferOverrun
                else:
                    if actual_param_id != param_id:
                        raise BadResponseParamID(module_id, param_id, actual_param_id)
                    if actual_module_id != module_id:
                        raise BadResponseModuleID(module_id, actual_module_id)
            else:
                return data_recovered
        return None

    @staticmethod
    def _validate_discovery_response(can_id_resp: int, data_resp: bytes) -> int:
        param_id = data_resp[-1] >> 1
        module_type = data_resp[0]
        module_id = can_id_resp - CAN_RESPONSE_BASE_ID
        if param_id != TX_PARAM_ID.DISCOVERY:
            raise BadResponseParamID(module_id, TX_PARAM_ID.DISCOVERY, param_id)
        if module_id < 0:
            raise BadResponseModuleID(0, module_id)
        if module_type not in DEVICE_TYPE:
            raise BadResponseDevType(module_type)
        return module_type

    def _write(self, module_id: int, param_id: IntEnum, data: int | None = None, size: int | None = None) -> None:
        for try_id in range(self._n_try):
            try:
                read = 0
                if data is not None:
                    data_send = int(data).to_bytes(size, 'little') + ((int(param_id) << 1) + read).to_bytes(1)
                else:
                    data_send = ((int(param_id) << 1) + read).to_bytes(1)
                self.backend.send(module_id, data_send)
                can_id_resp, data_resp = self.backend.receive()
                if can_id_resp is not None:
                    try:
                        self._validate_response(module_id, param_id, can_id_resp, data_resp)
                    except RxBufferOverrun:
                        warnings.warn('RxBufferOverrun exception occurred during write to module {0}!'.format(module_id))
                        if self._logger is not None:
                            self._logger.warning(f'RxBufferOverrun exception occurred during write to module {module_id}!')
                else:
                    if self._logger is not None:
                        self._logger.error(f"try_id = {try_id}", exc_info=True)
                    raise NoResponse(module_id)
                break
            except (NoResponse, BadResponseModuleID, BadResponseParamID) as exc:
                if self._logger is not None:
                    self._logger.error(f"try_id = {try_id}",exc_info=True)
                if try_id < self._n_try-1:
                    pass
                else:
                    raise exc
            except BackendRxFault as exc:
                if self._logger is not None:
                    self._logger.error(f"try_id = {try_id}",exc_info=True)
                if try_id < self._n_try - 1:
                    if self._logger is not None:
                        self._logger.info("Backend restart")
                    self.backend.close()
                    self._open_backend()
                    self._flush_rx_buffer()
                else:
                    raise exc

    def _read(self, module_id: int, param_id: IntEnum, size: int) -> int:
        for try_id in range(self._n_try):
            try:
                read = 1
                data = ((int(param_id) << 1) + read).to_bytes(1)

                self.backend.send(module_id, data)
                can_id_resp, data_resp = self.backend.receive()
                if can_id_resp is not None:
                    data_recovered = self._validate_response(module_id, param_id, can_id_resp, data_resp)
                    if data_recovered is not None:
                        data_resp = data_recovered
                    value = int.from_bytes(data_resp[0:size], 'little')
                    return value
                else:
                    raise NoResponse(module_id)
            except (NoResponse, BadResponseModuleID, BadResponseParamID) as exc:
                if self._logger is not None:
                    self._logger.error(f"try_id = {try_id}",exc_info=True)
                if try_id < self._n_try-1:
                    pass
                else:
                    raise exc
            except BackendRxFault as exc:
                if self._logger is not None:
                    self._logger.error(f"try_id = {try_id}",exc_info=True)
                if try_id < self._n_try - 1:
                    if self._logger is not None:
                        self._logger.info("Backend restart")
                    self.backend.close()
                    self._open_backend()
                    self._flush_rx_buffer()
                else:
                    raise exc

    def discovery(self):
        module_id = CAN_BROADCAST_ID
        param_id = TX_PARAM_ID.DISCOVERY
        read = 1
        data = ((int(param_id) << 1) + read).to_bytes(1)
        self.backend.send(module_id, data)
        result = []
        while 1 :
            can_id_resp, data_resp = self.backend.receive()
            if can_id_resp is None:
                break
            result += [(can_id_resp, data_resp)]
        for itm in result:
            print( self._validate_discovery_response( itm[0], itm[1] ) )