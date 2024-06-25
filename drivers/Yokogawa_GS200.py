from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument


class CurrentSource(VisaInstrument):
    def __init__(self, *args):
        VisaInstrument.__init__(self, *args)
        self.instr.write('SOUR:FUNC CURR')
        self.autorange = False

    def setpoint(self, val=None):
        if val is not None:
            if self.autorange:
                self.instr.write("SOUR:LEVEL:AUTO {:f}".format(val))
            else:
                self.instr.write("SOUR:LEVEL {:f}".format(val))
        else:
            val = float(self.instr.query("SOUR:LEVEL?"))
        return val

    def output(self, val=None):
        return int(self.write_or_query("OUTP", self.parse_on_off_val(val), "{:s}"))

    def limit(self, val=None):
        return float(self.write_or_query("SOUR:PROT:VOLT", val, "{:f}"))

    def range(self, val=None):
        return float(self.write_or_query("SOUR:RANG", val, "{:f}"))

    def autorange(self, val=None):
        if val is not None:
            if self.parse_on_off_val(val) == '1':
                self.autorange = True
            else:
                self.autorange = False
        return self.autorange

    def channel(self, val=None):
        """This instrument has 1 channel"""
        return 0
