from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument


class CurrentSource(VisaInstrument):
    def __init__(self, *args):
        VisaInstrument.__init__(self, *args)
        # Inner shield is "output low"
        if not self.output():
            self.instr.write("OUTP:ISH OLOW")
            # Output low can be connected to the chassis if "ON"
            self.instr.write("OUTP:LTE OFF")
        self.instr.write("SOUR:CURR:FILT ON")

    def setpoint(self, val=None):
        return float(self.write_or_query("SOUR:CURR", val, "{:e}"))

    def output(self, val=None):
        return int(self.write_or_query("OUTP:STAT", self.parse_on_off_val(val), "{:s}"))

    def limit(self, val=None):
        return float(self.write_or_query("SOUR:CURR:COMP", val, "{:e}"))

    def range(self, val=None):
        return float(self.write_or_query("SOUR:CURR:RANG", val, "{:e}"))

    def autorange(self, val=None):
        return int(self.write_or_query("SOUR:CURR:RANG:AUTO", self.parse_on_off_val(val), "{:s}"))

    def channel(self, val=None):
        """This instrument has 1 channel"""
        return 0
