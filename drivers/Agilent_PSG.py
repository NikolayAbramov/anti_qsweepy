# RF generator
from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
import time


class Generator(VisaInstrument):

    def __init__(self, *args):
        VisaInstrument.__init__(self, *args)
        self._ch = 0

    def channel(self, val: int|None = None) -> int:
        """Set active channel. There is only one channel 0 on this device."""
        if val is not None:
            if val != self._ch:
                raise ValueError('There is only one channel 0 on this device!')
        return self._ch

    def power(self, val: float|None = None) -> float:
        return float(self.write_or_query("POW", val, "{:f}"))

    def freq(self, val: float|None = None) -> float:
        return float(self.write_or_query("FREQ", val, "{:e}"))

    def phase(self, val: float|None = None) -> float:
        return float(self.write_or_query("PHASE", val, "{:e}"))

    def output(self, val: float|None = None) -> bool:
        val = self.write_or_query('OUTP', self.parse_on_off_val(val), "{:s}")
        if val == '1':
            return True
        else:
            return False
