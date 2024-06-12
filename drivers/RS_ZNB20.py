# Network analyzer
from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
import time


class NetworkAnalyzer(VisaInstrument):

    def __init__(self, *args):
        VisaInstrument.__init__(self, *args)
        self.instr.write('FORM REAL,32; FORM:BORD SWAP;')

    def s_parameter(self, val=None):
        # Mtype = "S11"|"S21"|"S22"|"S12"
        # Select measurement before doing this
        if val is not None:
            self.instr.write("CALC:PAR:MEAS 'Trc1','S{:s}{:s}'".format(str(val[0]), str(val[1])))
        else:
            val = self.instr.query("CALC:PAR:CAT?")
        return val

    def soft_trig_arm(self):
        self.instr.write("INIT:CONT OFF")
        self.instr.write("*ESE 1")

    def read_data(self):
        if int(self.instr.query('SENS1:AVER:STAT?')) == 1:
            n_aver = int(self.instr.query("AVER:COUN?"))
            self.instr.write('AVER:CLE')
        else:
            n_aver = 1
        for i in range(n_aver):
            # Clear status, initiate measurement
            self.instr.write("*CLS")
            self.instr.write("INIT:ALL")
            self.instr.write("*OPC")
            # Set bit in ESR when operation complete
            while not (int(self.instr.query("*ESR?")) & 1):
                time.sleep(0.002)

        data = self.instr.query_binary_values("CALC:DATA? SDATA", datatype=u'f')
        data_size = size(data)
        return array(data[0:data_size:2]) + 1.j * array(data[1:data_size:2])

    def soft_trig_abort(self):
        self.instr.write("INIT:CONT ON")

    def power(self, val=None):
        return float(self.write_or_query("SOUR:POW", val, "{:f}"))

    def output(self, val=None):
        return (self.write_or_query('OUTP', self.parse_on_off_val(val), "{:s}"))

    def bandwidth(self, val=None):
        return int(self.write_or_query("SENS1:BAND", val, "{:f}"))

    def freq_start_stop(self, val=None):
        if val is not None:
            self.instr.write("SENS1:FREQ:START {:e}".format(val[0]))
            self.instr.write("SENS1:FREQ:STOP {:e}".format(val[1]))
        else:
            val = [0, 0]
            val[0] = self.instr.query("SENS1:FREQ:START?")
            val[1] = self.instr.query("SENS1:FREQ:STOP?")
        return val

    def freq_center_span(self, val=None):
        if val is not None:
            self.instr.write("SENS1:FREQ:CENT {:e}".format(val[0]))
            self.instr.write("SENS1:FREQ:SPAN {:e}".format(val[1]))
        else:
            val = [0, 0]
            val[0] = float(self.instr.query("SENS1:FREQ:CENT?"))
            val[1] = float(self.instr.query("SENS1:FREQ:SPAN?"))
        return val

    def freq_cw(self, val=None):
        return float(self.write_or_query('SENS1:FREQ:CW', val, "{:e}"))

    def freq_points(self):
        return array(self.instr.query_binary_values('CALC:DATA:STIM?', datatype=u'f'))

    def sweep_type(self, val=None):
        if val is not None:
            # Actually, POINT is you usual expected CW mode
            # CW here is wierd "time" sweep and cause software trigger failure
            val = val.upper()
            if val == "CW": val = "POINT"
            if val not in ["LIN", "LOG", "POW", "CW", "POINT", "SEGM", "PULS"]:
                raise ValueError('Sweep type mode must be LIN | LOG | POW | CW | SEGM | PHASE')
        return self.write_or_query("SENS1:SWE:TYPE", val, "{:s}")

    def num_of_points(self, val=None):
        return float(self.write_or_query("SENS1:SWE:POIN", int(val), "{:d}"))

    def averaging(self, val=None):
        if val is not None:
            if val > 1:
                self.instr.write('SENS:AVER:STAT ON')
                self.instr.write('SENS:AVER:COUN {:d}'.format(val))
            else:
                self.instr.write('SENS:AVER:STAT OFF')
        else:
            if int(self.instr.query('SENS:AVER:STAT?')):
                val = int(self.instr.query('SENS:AVER:COUN?'))
            else:
                val = 0
        return val


'''			
		return int(self.write_or_query('SENS:AVER:STAT', self.parse_on_off_val(val), "{:s}"))
	
	def averaging_count(self, val = None):
		return int(self.write_or_query('SENS:AVER:COUN', int(val), '{:d}'))
		
'''
