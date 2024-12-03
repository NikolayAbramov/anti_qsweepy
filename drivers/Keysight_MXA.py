import numpy as np
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument


class SpectrumAnalyzer(VisaInstrument):
    """This general purpose Spectrum Analyzer representation of the Keysight MXA"""

    def __init__(self, *args):
        VisaInstrument.__init__(self, *args)
        # Make sure that mode is SAN = Spectrum Analyzer
        if 'SAN' not in self.query("CONF?"):
            self.write("CONF:SAN")
        # Set detector type "Average"
        self.instr.write(':DET:TRAC AVER')

    def soft_trig_arm(self):
        self.instr.write(':INIT:CONT OFF')
        pass

    def soft_trig_abort(self):
        self.instr.write(':INIT:CONT ON')
        pass

    def read_data(self):
        """Returns measured spectrum in watts"""
        self.instr.query(':INIT:IMM;*OPC?')
        buffer = self.instr.query("CALC:DATA?")
        data = np.fromstring(buffer, sep=",", dtype=float)
        S = data[1::2]
        F = data[0::2]
        S = 10 ** (S / 10) * 1e-3
        return S

    def rbw(self, val=None):
        '''
        Resolution bandwidth
        '''
        if val is not None:
            self.instr.write(":BAND {:e}".format(val))
        else:
            val = float(self.instr.query(":BAND?"))
        return val

    def vbw(self, val=None):
        '''
        Video bandwidth
        '''
        if val is not None:
            self.instr.write(":BAND:VID {:e}".format(val))
        else:
            val = float(self.instr.query(":BAND:VID?"))
        return val

    def ref_level(self, val=None):
        if val is not None:
            self.instr.write(":DISP:WIND:TRAC:Y:RLEV {:e}".format(val))
        else:
            val = float(self.instr.query(":DISP:WIND:TRAC:Y:RLEV?"))
        return val

    def freq_start_stop(self, val=None):
        if val is not None:
            self.instr.write(":FREQ:STAR {:e}".format(val[0]))
            self.instr.write(":FREQ:STOP {:e}".format(val[1]))
        else:
            val = [0, 0]
            val[0] = float(self.instr.query(":FREQ:STAR?"))
            val[1] = float(self.instr.query(":FREQ:STOP?"))
        return val

    def freq_center_span(self, val=None):
        if val is not None:
            self.instr.write(":FREQ:CENT {:e}".format(val[0]))
            self.instr.write(":FREQ:SPAN {:e}".format(val[1]))
        else:
            val = [0, 0]
            val[0] = float(self.instr.query(":FREQ:CENT?"))
            val[1] = float(self.instr.query(":FREQ:SPAN?"))
        return val

    def freq_points(self):
        """Get frequency points from the instrumen. Only available when sweep is complete."""
        buffer = self.instr.query("CALC:DATA?")
        data = np.fromstring(buffer, sep=",", dtype=float)
        F = data[0::2]
        return F

    def averaging(self, val=None):
        # Not supported
        return 1


class ListSpectrumAnalyzer(VisaInstrument):
    """List sweeping Spectrum Analyzer representation of the Keysight MXA"""
    def __init__(self, *args):
        VisaInstrument.__init__(self, *args)
        # Make sure mode is LIST
        if self.query(":CONF?") != "LIST":
            self.write(":CONF:LIST")
        self.write(':LIST:DET RMS')

    def sweep_time(self, val: float | None =None) -> float:
        return float(self.write_or_query(':LIST:SWE:TIME', val, "{:e}"))

    def freq_points(self, freq_list=None) -> np.ndarray[float]:
        """Sets or gets list of frequencies in Hz"""
        if freq_list is not None:
            self.write(':LIST:FREQ ' + ', '.join('{:e}'.format(f) for f in freq_list))
        else:
            freq_list = np.asarray(self.query(':LIST:FREQ?').split(','), dtype=float)
        return freq_list

    def rbw(self, val: float | None = None) -> float:
        return float(self.write_or_query(':LIST:BAND:RES', val, "{:e}"))

    def vbw(self, val: float | None = None) -> float:
        return float(self.write_or_query(':LIST:BAND:VID', val, "{:e}"))

    def read_data(self) -> np.ndarray[float]:
        """Starts measurement and returns measured power in dBm"""
        return np.asarray(self.query(':READ:LIST?').split(','), dtype=float)
