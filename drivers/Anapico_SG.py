# Driver for AnaPico RF generators

from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
from anti_qsweepy.drivers import exceptions


class Generator(VisaInstrument):

    def __init__(self, *args):
        VisaInstrument.__init__(self, *args)

    def channels(self) -> int:
        """Returns number of channels"""
        max_it = 20
        n_it = 0
        ch_id = 0
        n_ch = 0
        while 1:
            try:
                self.channel(ch_id)
                n_ch += 1
            except exceptions.ChIndexOutOfRange:
                if ch_id != 0:
                    break
            ch_id += 1
            if n_it >= max_it:
                raise Exception("Can't get number of channels for AnaPico SG device!")
            n_it += 1
        return n_ch

    def channel(self, val: int | None = None) -> int:
        """Select active channel"""
        if val is not None:
            self.write(":SEL {:d}".format(val))
        ch = int(self.query(":SEL?"))
        if val is not None:
            if ch != val:
                raise exceptions.ChIndexOutOfRange("Channel index {0} is out of range!".format(val))
        return ch

    def power(self, val: float | None = None) -> float:
        """Returns power in dBm"""
        return float(self.write_or_query("SOUR:POW", val, "{:f}"))

    def freq(self, val: float | None = None) -> float:
        """Returns frequency in Hz"""
        return float(self.write_or_query("FREQ", val, "{:e}"))

    def phase(self, val: float | None = None) -> float:
        """Returns phase in deg"""
        if val is not None:
            val = val/180*pi
        return float(self.write_or_query("SOUR:PHASE", val, "{:e}"))

    def output(self, val: bool | None = None) -> bool:
        """Returns output state"""
        return bool(int(self.write_or_query('OUTP', self.parse_on_off_val(val), "{:s}")))
