from .instrument_base_classes import VisaInstrument


class CurrentSource(VisaInstrument):
    """Yokogawa GS200 as current source"""
    def __init__(self, *args):
        VisaInstrument.__init__(self, *args)
        self.instr.write('SOUR:FUNC CURR')
        self.autorange = False

    def setpoint(self, val:float|None = None)->float:
        """Set current or voltage setpoint"""
        if val is not None:
            if self.autorange:
                self.instr.write("SOUR:LEVEL:AUTO {:f}".format(val))
            else:
                self.instr.write("SOUR:LEVEL {:f}".format(val))
        else:
            val = float(self.instr.query("SOUR:LEVEL?"))
        return val

    def output(self, val:bool|None = None)->bool:
        """Turn output on/off"""
        return bool(int(self.write_or_query("OUTP", self.parse_on_off_val(val), "{:s}", check=True)))

    def limit(self, val=None)->float:
        """Set voltage limit"""
        return float(self.write_or_query("SOUR:PROT:VOLT", val, "{:f}", check=True))

    def range(self, val:float|None = None)->float:
        """Set source range"""
        return float(self.write_or_query("SOUR:RANG", val, "{:f}", check=True))

    def autorange(self, val=None):
        """Turn on/off auto-range"""
        if val is not None:
            if self.parse_on_off_val(val) == '1':
                self.autorange = True
            else:
                self.autorange = False
        return self.autorange

    def channel(self, val=None):
        """This instrument has 1 channel"""
        return 0

class VoltageSource(CurrentSource):
    """Yokogawa GS200 as voltage source"""
    def __init__(self, *args):
        VisaInstrument.__init__(self, *args)
        self.instr.write('SOUR:FUNC VOLT')
        self.autorange = False

    def limit(self, val:float|None = None)->float:
        """Set current limit"""
        return float(self.write_or_query("SOUR:PROT:CURR", val, "{:f}", check=True))