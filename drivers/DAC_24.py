from numpy import *
import warnings
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument


class CurrentSource(VisaInstrument):
    """Current source with differential outputs"""

    def __init__(self, *args):
        VisaInstrument.__init__(self, *args, term_chars='\n')
        self.always_query = True
        self.Vmax = 4.096
        # Value of filter resistors in the box for each channel
        self.resistance = [270 * 4, 270 * 4, 270 * 4, 270 * 4,
                           270 * 4, 270 * 4, 270 * 4, 270 * 4,
                           270 * 4, 270 * 4, 270 * 4, 270 * 4]
        self.ch_plus = 0
        self.ch_minus = 1
        self.ch = 0
        # Number of channels
        self._n_ch = 12

    def channel(self, val=None):
        """Sets active channel"""
        if val is not None:
            val = int(val)
            if val >= self._n_ch or val < 0:
                raise ValueError("Channel id is out of range!")
            self.ch_plus = val * 2
            self.ch_minus = val * 2 + 1
            self.ch = val
        return self.ch

    def setpoint(self, val: float|None = None) -> float:
        """Current setpoint, A."""
        if val is not None:
            V = val * self.resistance[self.ch]
            if abs(V) > self.Vmax * 2:
                warnings.warn("Out of range!")
            self.query("volt {:s},{:e}".format(str(self.ch_plus), V / 2))
            self.query("volt {:s},{:e}".format(str(self.ch_minus), -V / 2))

        Vplus = float(self.query("volt {:s}?".format(str(self.ch_plus))))
        Vminus = float(self.query("volt {:s}?".format(str(self.ch_minus))))
        # Return actual I set
        return (Vplus - Vminus) * self.resistance[self.ch]

    def output(self, val=None):
        """Output on/off is not supported"""
        if val is None:
            return True

    def limit(self, val=None):
        """Limit is fixed."""
        if val is None:
            return self.Vmax * 2

    def range(self, val=None):
        """Range is fixed."""
        if val is None:
            return self.Vmax * 2 / self.resistance[self.ch]

    def autorange(self, val=None):
        """Autorange is not supported"""
        if val is None:
            return False
