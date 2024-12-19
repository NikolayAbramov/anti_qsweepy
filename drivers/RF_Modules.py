import warnings
from enum import Enum

from anti_qsweepy.drivers.rf_modules.definitions import *


class NoResponse(Exception):
    def __init__(self, module_id: int):
        msg = 'Module ID: '+str(module_id)
        super().__init__(msg)


class BadResponseModuleID(Exception):
    def __init__(self, module_id: int, actual_id: int):
        msg = 'Module ID must be {0} , got {1} instead'.format(module_id, actual_id)
        super().__init__(msg)


class BadResponseParamID(Exception):
    def __init__(self, module_id: int, param_id: int, actual_param_id: int):
        msg = 'Module ID: {0}. Parameter ID must be {1} , got {2} instead'.format(module_id, param_id, actual_param_id)
        super().__init__(msg)


class RxBufferOverrun(Exception):
    def __init__(self):
        msg = 'Try again'
        super().__init__(msg)

class BACKENDS(Enum):
    WAVESHARE_USB_CAN_A = 1
    PYTHON_CAN_GS_USB = 2

class TX:
    def __init__(self, addr:str, backend:BACKENDS = BACKENDS.WAVESHARE_USB_CAN_A):
        self.timeout = 1
        filters = {"can_id": CAN_RESPONSE_BASE_ID, "can_mask": CAN_RESPONSE_BASE_ID}
        if backend is BACKENDS.WAVESHARE_USB_CAN_A:
            from anti_qsweepy.drivers.rf_modules.waveshare_usb_can_a import WaveshareUSB_CAN_A
            self.backend = WaveshareUSB_CAN_A(addr, 2000000, 500000)
        elif backend is BACKENDS.PYTHON_CAN_GS_USB:
            from anti_qsweepy.drivers.rf_modules.python_can_backend import PythonCAN_GS_USB_Backend
            self.backend = PythonCAN_GS_USB_Backend(filters)
        self.flush_rx_buffer()

    def flush_rx_buffer(self, module_id: int|None = None, param_id: int|None = None) -> tuple[int,bytes|None]:
        """Flush RX buffer of the adapter and try to find lost message if corresponding parameters of the function are provided"""
        msg_flushed = 0
        self.backend.timeout = 0.1
        data_recovered = None
        for _ in range(100):
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
        self._write(module_id, PARAM_ID.MODULE_ID)

    @staticmethod
    def _mixer_offset_dac_code(val: float) -> int:
        """Valid val range is from -1 to 1"""
        if val > 1.0:
            val = 1.0
        if val < -1.0:
            val = -1.0
        val = int(round((val+1)*MIXER_OFFSET_DAC_MIDDLE))
        if val>MIXER_OFFSET_DAC_MAX:
            val = MIXER_OFFSET_DAC_MAX
        return val

    @staticmethod
    def _mixer_offset_norm(val: int ) -> float:
        val = ( float(val) - float(MIXER_OFFSET_DAC_MIDDLE) ) / float(MIXER_OFFSET_DAC_MIDDLE)
        return val

    def mixer_offsets(self, module_id: int, offsets: tuple[float, float] | None = None) -> tuple[float, float]:
        """Set mixer DC offsets in arbitrary units in range from -1 to 1.

        Values outside the range are clipped.
        """

        if offsets is not None:
            int_offset_0 = self._mixer_offset_dac_code(offsets[0])
            int_offset_1 = self._mixer_offset_dac_code(offsets[1])
            param_id = PARAM_ID.MIXER_OFFSETS
            dac_data = int_offset_0 + (int_offset_1 << 12)
            self._write(module_id, param_id, dac_data, 3)
        else:
            offsets_data = self._read(module_id, PARAM_ID.MIXER_OFFSETS, 3)
            offset_0 = self._mixer_offset_norm( offsets_data & 0xFFF )
            offset_1 = self._mixer_offset_norm( offsets_data >> 12 )
            offsets = (offset_0, offset_1)
        return offsets

    def bias(self, module_id: int, val: float|None = None) -> float:
        """Set DC bias in Volts at the output

        Bias range is -1.65 to 1.65 V on a 50 Ohm load. Values outside the range are clipped."""
        if val is not None:
            code = int( round( (val+BIAS_DAC_VREF/2) / BIAS_DAC_VREF * (BIAS_DAC_MAX+1) ) )
            if code > BIAS_DAC_MAX:
                code = BIAS_DAC_MAX
            if code<0:
                code = 0
            self._write(module_id, PARAM_ID.BIAS, code, 2)
        else:
            code = self._read(module_id, PARAM_ID.BIAS, 2)
            val = BIAS_DAC_VREF*code/(BIAS_DAC_MAX+1) - BIAS_DAC_VREF/2
        return val

    def external_bias(self, module_id: int, state: bool | None = None) -> bool:
        """Choose between internal bias if False and external bias if True"""

        if state is not None:
            self._write(module_id, PARAM_ID.BIAS_SELECT, int(state), 1)
        else:
            state = bool(self._read(module_id, PARAM_ID.BIAS_SELECT, 1))
        return state

    def lo_amp_pwr(self, module_id: int, state: bool | None = None) -> bool:
        """Turn ON/OFF LO amplifier

        This function is useless.You may not use it at all."""

        if state is not None:
            self._write(module_id, PARAM_ID.LO_AMP_PWR, int(state), 1)
        else:
            state = bool(self._read(module_id, PARAM_ID.LO_AMP_PWR, 1))
        return state

    def mixer_bypass(self, module_id: int, state: bool | None = None) -> bool:
        """Turn mixer bypass ON/OFF

        Bypass mode intended to be used for spectroscopy. In this mode LO signal is
        passes to the output bypassing the mixer."""
        if state is not None:
            self._write(module_id, PARAM_ID.MIXER_BYPASS, int(state), 1)
        else:
            state = bool(self._read(module_id, PARAM_ID.MIXER_BYPASS, 1))
        return state

    def rf_output(self, module_id: int, state: bool | None = None) -> bool:
        """ON/OFF RF signal at the output

        Does not affect DC bias.
        """
        if state is not None:
            self._write(module_id, PARAM_ID.RF_OUTPUT, int(state), 1)
        else:
            state = bool(self._read(module_id, PARAM_ID.RF_OUTPUT, 1))
        return state

    def lo_attenuation(self, module_id: int, val: float | None = None) -> float:
        """Set LO attenuation in dB

        Maximal attenuation is 31.5 dB, minimal is 0 dB. If value is outside the range it's clipped to
        31.5 or 0 dB. Step is equal to 0.5 dB therefore the value is rounded accordingly. In bypass mode
        attenuation can be used to control second tone power for spectroscopy.
        """
        if val is not None:
            code = int( round(val/0.5) )
            if code > LO_ATT_MAX:
                code = LO_ATT_MAX
            if code < 0:
                code = 0
            self._write(module_id, PARAM_ID.LO_ATT, code, 1)
        else:
            code = self._read(module_id, PARAM_ID.LO_ATT, 1)
        val = code * LO_ATT_STEP
        return val

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

    def _write(self, module_id: int, param_id: PARAM_ID, data: int | None = None, size: int | None = None) -> None:
        read = 0
        if data is not None:
            data = int(data).to_bytes(size, 'little') + ((int(param_id) << 1) + read).to_bytes(1)
        else:
            data = ((int(param_id) << 1) + read).to_bytes(1)
        self.backend.send(module_id, data)
        can_id_resp, data_resp = self.backend.receive()
        if can_id_resp is not None:
            try:
                self._validate_response(module_id, param_id, can_id_resp, data_resp)
            except RxBufferOverrun:
                warnings.warn('RxBufferOverrun exception occurred during write to module {0}!'.format(module_id))
        else:
            raise NoResponse(module_id)

    def _read(self, module_id: int, param_id: PARAM_ID, size: int) -> int:
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