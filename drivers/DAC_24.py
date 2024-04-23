from numpy import *
import warnings
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
from dataclasses import dataclass


@dataclass
class ChannelData:
    ch_plus: int
    ch_minus: int
    v_plus: float = 0
    v_minus: float = 0
    output: bool = True

class CurrentSource(VisaInstrument):
    """Current source with differential outputs"""
    def __init__(self, *args):
        VisaInstrument.__init__(self, *args, term_chars='\n')
        self.always_query = True
        self.Vmax = 4.094
        self.Vmin = -4.096
        self.dac_bit = 12
        self.Vres = 0.002
        # Value of filter resistors in the box for each channel
        self.resistance = [270 * 4, 270 * 4, 270 * 4, 270 * 4,
                           270 * 4, 270 * 4, 270 * 4, 270 * 4,
                           270 * 4, 270 * 4, 270 * 4, 270 * 4]
        self.ch = 0
        # Number of channels
        self._n_ch = 12
        self._output_state = [True] * self._n_ch
        # Voltage buffer
        self._ch_data: list[ChannelData] = []
        for ch in range(self._n_ch):
            ch_plus, ch_minus = self._get_plus_minus_ch(ch)
            self._ch_data += [ChannelData(ch_plus=ch_plus,
                                          ch_minus=ch_minus)]
        for ch, ch_data in enumerate(self._ch_data):
            v_plus, v_minus = self._get_difff_voltages(ch)
            ch_data.v_plus = v_plus
            ch_data.v_minus = v_minus
            if v_plus == 0 and v_minus == 0:
                ch_data.output = False

    def _get_plus_minus_ch(self, ch: int) -> tuple[int, int]:
        ch_plus = ch * 2
        ch_minus = ch_plus + 1
        return ch_plus, ch_minus

    def _get_difff_voltages(self, ch: int) -> tuple[float, float]:
        ch_plus = self._ch_data[ch].ch_plus
        ch_minus = self._ch_data[ch].ch_minus
        v_plus = float(self.query("volt {:s}?".format(str(ch_plus))))
        v_minus = float(self.query("volt {:s}?".format(str(ch_minus))))
        return v_plus, v_minus

    def _set_diff_voltages(self, v_plus: float, v_minus: float, ch: int) -> None:
        ch_plus = self._ch_data[ch].ch_plus
        ch_minus = self._ch_data[ch].ch_minus
        self.query("volt {:s},{:e}".format(str(ch_plus), v_plus))
        self.query("volt {:s},{:e}".format(str(ch_minus), v_minus))

    def channel(self, val: int = None) -> int:
        """Sets active channel"""
        if val is not None:
            val = int(val)
            if val >= self._n_ch or val < 0:
                raise ValueError("Channel id is out of range!")
            self.ch = val
        return self.ch

    def setpoint(self, val: float | None = None) -> float:
        """Current setpoint, A."""
        if val is not None:
            V = val * self.resistance[self.ch]
            if abs(V) > (self.Vmax - self.Vmin):
                warnings.warn("Out of range!")
            n = round(V/self.Vres)
            if n%2 == 0.0:
                Vplus = self.Vres * n/2
                Vminus = -Vplus
            else:
                Vplus = self.Vres * (0.5 + n/2)
                Vminus = -Vplus + self.Vres
            if self._ch_data[self.ch].output:
                self._set_diff_voltages(Vplus, Vminus, self.ch)
            else:
                self._set_diff_voltages(0, 0, self.ch)
                self._ch_data[self.ch].v_plus = Vplus
                self._ch_data[self.ch].v_minus = Vminus
        Vplus, Vminus = self._get_difff_voltages(self.ch)
        if self._ch_data[self.ch].output:
            self._ch_data[self.ch].v_plus = Vplus
            self._ch_data[self.ch].v_minus = Vminus
        else:
            # Check if it's actually off
            if Vplus == 0 and Vminus == 0:
                Vplus = self._ch_data[self.ch].v_plus
                Vminus = self._ch_data[self.ch].v_minus
            else:
                # If somehow it's on
                self._ch_data[self.ch].output = True
                self._ch_data[self.ch].v_plus = Vplus
                self._ch_data[self.ch].v_minus = Vminus
        # Return actual I set
        return (Vplus - Vminus) / self.resistance[self.ch]

    def output(self, val: bool | None = None) -> bool:
        """Output on/off"""
        if val is not None:
            if not val:
                # OFF
                self._ch_data[self.ch].v_plus, self._ch_data[self.ch].v_minus = \
                    self._get_difff_voltages(self.ch)
                self._set_diff_voltages(0, 0, self.ch)
            else:
                # ON
                # First, check if it's actually off
                v_plus, v_minus = self._get_difff_voltages(self.ch)
                if v_plus == 0 and v_minus == 0:
                    # If it's off then restore saved voltages
                    self._set_diff_voltages(self._ch_data[self.ch].v_plus, self._ch_data[self.ch].v_minus, self.ch)
                else:
                    # If it's on then don't touch
                    self._ch_data[self.ch].v_plus = v_plus
                    self._ch_data[self.ch].v_minus = v_minus
            self._ch_data[self.ch].output = val
        return self._ch_data[self.ch].output

    def limit(self, val: float | None = None) -> float:
        """Limit is fixed."""
        return self.Vmax - self.Vmin

    def range(self, val: float | None = None) -> float:
        """Range is fixed."""
        return self.Vmax * 2 / self.resistance[self.ch]

    def autorange(self, val: bool | None = None) -> bool:
        """Autorange is not supported"""
        return False
