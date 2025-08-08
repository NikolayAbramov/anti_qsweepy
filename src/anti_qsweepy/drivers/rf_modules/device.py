import warnings
from enum import Enum, auto

from .definitions import *
from .exceptions import *

class BACKENDS(Enum):
    WAVESHARE_USB_CAN_A = 1
    PYTHON_CAN_GS_USB = 2

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
    def __init__(self, addr:str, backend:BACKENDS = BACKENDS.WAVESHARE_USB_CAN_A):
        self._addr = addr
        self._backend_type = backend
        self.timeout = 1
        self.n_try = 3
        self._open_backend()
        self.flush_rx_buffer()

    def _open_backend(self):
        filters = {"can_id": CAN_RESPONSE_BASE_ID, "can_mask": CAN_RESPONSE_BASE_ID}
        if self._backend_type is BACKENDS.WAVESHARE_USB_CAN_A:
            from .waveshare_usb_can_a import WaveshareUSB_CAN_A
            self.backend = WaveshareUSB_CAN_A(self._addr, 2000000, 500000)
        elif self._backend_type is BACKENDS.PYTHON_CAN_GS_USB:
            from .python_can_backend import PythonCAN_GS_USB_Backend
            self.backend = PythonCAN_GS_USB_Backend(filters)

    def flush_rx_buffer(self, module_id: int|None = None, param_id: int|None = None) -> tuple[int,bytes|None]:
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

    def module_id(self, module_id: int):
        """Identify module by initiating its green LED blinking"""
        self._write(module_id, TX_PARAM_ID.MODULE_ID)

    def device_type(self, module_id: int)->DEVICE_TYPE:
        """Get module type"""
        return DEVICE_TYPE(self._read(module_id, TX_PARAM_ID.DEVICE_TYPE, 1))

    def _validate_response(self, module_id: int, param_id: int, can_id_resp: int, data_resp: bytes) -> bytes|None:
        actual_param_id = data_resp[-1] >> 1
        actual_module_id = can_id_resp - CAN_RESPONSE_BASE_ID
        if actual_param_id != param_id or actual_module_id != module_id:
            msg_flushed, data_recovered = self.flush_rx_buffer(module_id, param_id)
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
        for try_id in range(self.n_try):
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
                else:
                    raise NoResponse(module_id)
                break
            except (NoResponse, BadResponseModuleID, BadResponseParamID) as exc:
                if try_id < self.n_try-1:
                    pass
                else:
                    raise exc
            except BackendRxFault as exc:
                if try_id < self.n_try - 1:
                    self.backend.close()
                    self._open_backend()
                    self.flush_rx_buffer()
                else:
                    raise exc

    def _read(self, module_id: int, param_id: IntEnum, size: int) -> int:
        for try_id in range(self.n_try):
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
                if try_id < self.n_try-1:
                    pass
                else:
                    raise exc
            except BackendRxFault as exc:
                if try_id < self.n_try - 1:
                    self.backend.close()
                    self._open_backend()
                    self.flush_rx_buffer()
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