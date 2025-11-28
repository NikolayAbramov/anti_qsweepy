from debugpy.launcher import channel

from .rf_modules.definitions import *
from .rf_modules.device import Device
from .rf_modules.device import BACKENDS
from .rf_modules.python_can_backend import PythonCAN_GS_USB_Backend
from .rf_modules.waveshare_usb_can_a import WaveshareUSB_CAN_A

class RF_Modules(Device):
    """Compound device for RX an TX modules"""
    def __init__(self, addr:str,backend:BACKENDS = BACKENDS.WAVESHARE_USB_CAN_A,
                 rx_channels:list[int]|int = None, tx_channels:list[int]|int = None):
        super().__init__(addr, backend)
        self.RX : RX = RX(self.backend, channels=rx_channels)
        self.TX : TX = TX(self.backend, channels=tx_channels)

class TX(Device):
    """ Driver for the upconverting modules controlled via CAN

    When calling constructor to replace an existing object Please use del to delete it first:

    try:
        del obj
    except:
        pass
    obj  = TX()

    Otherwise, driver will be kept locked and new object will not work.
    """
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

    def mixer_offsets(self, offsets: tuple[float, float] | None = None) -> tuple[float, float]:
        """Set mixer DC offsets in arbitrary units in range from -1 to 1.

        Values outside the range are clipped.
        """

        if offsets is not None:
            int_offset_0 = self._mixer_offset_dac_code(offsets[0])
            int_offset_1 = self._mixer_offset_dac_code(offsets[1])
            param_id = TX_PARAM_ID.MIXER_OFFSETS
            dac_data = int_offset_0 + (int_offset_1 << 12)
            self._write(self._ch, param_id, dac_data, 3)
        else:
            offsets_data = self._read(self._ch, TX_PARAM_ID.MIXER_OFFSETS, 3)
            offset_0 = self._mixer_offset_norm( offsets_data & 0xFFF )
            offset_1 = self._mixer_offset_norm( offsets_data >> 12 )
            offsets = (offset_0, offset_1)
        return offsets

    def bias(self, val: float|None = None) -> float:
        """Set DC bias in Volts at the output

        Bias range is -1.65 to 1.65 V on a 50 Ohm load. Values outside the range are clipped."""
        if val is not None:
            code = int( round( (val+BIAS_DAC_VREF/2) / BIAS_DAC_VREF * (BIAS_DAC_MAX+1) ) )
            if code > BIAS_DAC_MAX:
                code = BIAS_DAC_MAX
            if code<0:
                code = 0
            self._write(self._ch, TX_PARAM_ID.BIAS, code, 2)
        else:
            code = self._read(self._ch, TX_PARAM_ID.BIAS, 2)
            val = BIAS_DAC_VREF*code/(BIAS_DAC_MAX+1) - BIAS_DAC_VREF/2
        return val

    def external_bias(self, state: bool | None = None) -> bool:
        """Choose between internal bias if False and external bias if True"""

        if state is not None:
            self._write(self._ch, TX_PARAM_ID.BIAS_SELECT, int(state), 1)
        else:
            state = bool(self._read(self._ch, TX_PARAM_ID.BIAS_SELECT, 1))
        return state

    def lo_amp_pwr(self, state: bool | None = None) -> bool:
        """Turn ON/OFF LO amplifier

        This function is useless.You may not use it at all."""

        if state is not None:
            self._write(self._ch, TX_PARAM_ID.LO_AMP_PWR, int(state), 1)
        else:
            state = bool(self._read(self._ch, TX_PARAM_ID.LO_AMP_PWR, 1))
        return state

    def mixer_bypass(self, state: bool | None = None) -> bool:
        """Turn mixer bypass ON/OFF

        Bypass mode intended to be used for spectroscopy. In this mode LO signal is
        passes to the output bypassing the mixer."""
        if state is not None:
            self._write(self._ch, TX_PARAM_ID.MIXER_BYPASS, int(state), 1)
        else:
            state = bool(self._read(self._ch, TX_PARAM_ID.MIXER_BYPASS, 1))
        return state

    def rf_output(self, state: bool | None = None) -> bool:
        """ON/OFF RF signal at the output

        Does not affect DC bias.
        """
        if state is not None:
            self._write(self._ch, TX_PARAM_ID.RF_OUTPUT, int(state), 1)
        else:
            state = bool(self._read(self._ch, TX_PARAM_ID.RF_OUTPUT, 1))
        return state

    def lo_attenuation(self, val: float | None = None) -> float:
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
            self._write(self._ch, TX_PARAM_ID.LO_ATT, code, 1)
        else:
            code = self._read(self._ch, TX_PARAM_ID.LO_ATT, 1)
        val = code * LO_ATT_STEP
        return val

class RX(Device):
    """ Driver for the downconverting modules controlled via CAN

    When calling constructor to replace an existing object, please use del to delete it first:

    try:
        del obj
    except:
        pass
    obj  = TX()

    Otherwise, the driver will be kept locked and the new object will not work.
    """
    def input_attenuation(self, val: float | None = None):
        """Set or get input attenuation in dB"""
        if val is not None:
            code = int( round(val/RX_INP_ATT_STEP) )
            if code > RX_INP_ATT_MAX_CODE:
                code = RX_INP_ATT_MAX_CODE
            if code < 0:
                code = 0
            self._write(self._ch, RX_PARAM_ID.INP_ATT, code, 1)
        else:
            code = self._read(self._ch, RX_PARAM_ID.INP_ATT, 1)
        val = code * RX_INP_ATT_STEP
        return val

    def is_local(self):
        """Get "local" status. If status is True, then the device is in "local" mode and inpt attenuation
        is controlled by means of the onboard DIP switch SW2. In the "local" mode attempts to set input attenuation
        will be ignored, but current value set by the DIP switch can be retrieved."""
        return bool( self._read(self._ch, RX_PARAM_ID.LOCAL, 1) )