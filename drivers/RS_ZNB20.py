#Network analyzer
from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
import time

class NetworkAnalyzer(VisaInstrument):

	def __init__(self, *args):
		VisaInstrument.__init__(self, *args)
		self.instr.write('FORM REAL,32; FORM:BORD SWAP;')

	def s_parameter(self, val = None):
		#Mtype = "S11"|"S21"|"S22"|"S12"
		#Select measurement before doing this
		if val is not None:
			self.instr.write( "CALC:PAR:MEAS 'Trc1','S{:s}{:s}'".format(str(val[0]), str(val[1])) )
		else:
			val = self.instr.query( "CALC:PAR:CAT?")
		return val

	def soft_trig_arm(self):
		self.instr.write("INIT:CONT OFF")
		self.instr.write("*ESE 1")
	
	def read_data(self):
		if int(self.instr.query('SENS1:AVER:STAT?'))==1:
			n_aver = int(self.instr.query("AVER:COUN?"))
			self.instr.write('AVER:CLE')
		else:
			n_aver = 1
		for i in range(n_aver):
			#Clear status, initiate measurement
			self.instr.write("*CLS")
			self.instr.write("INIT:ALL")
			self.instr.write("*OPC")
			#Set bit in ESR when operation complete
			while not( int(self.instr.query("*ESR?") ) & 1 ) :
				time.sleep(0.002)
		
		data = self.instr.query_binary_values("CALC:DATA? SDATA", datatype=u'f') 
		data_size = size(data)
		return array(data[0:data_size:2])+1.j*array(data[1:data_size:2])
	
	def soft_trig_abort(self):
		self.instr.write("INIT:CONT ON")
		
	def power(self, val = None):
		return float(self.write_or_query("SOUR:POW", val, "{:f}"))
	
	def output(self, val=None):
		return(self.write_or_query( 'OUTP', self.parse_on_off_val(val), "{:s}" ) )
	
	def bandwidth(self, val = None):
		return int(self.write_or_query("SENS1:BAND", val, "{:f}"))
		
	def freq_start(self, val=None):
		return float(self.write_or_query("SENS1:FREQ:START", val, "{:e}"))
		
	def freq_stop(self, val=None):
		return float(self.write_or_query("SENS1:FREQ:STOP", val, "{:e}"))
		
	def freq_center(self, val=None):
		return float(self.write_or_query("SENS1:FREQ:CENT", val, "{:e}"))
		
	def freq_span(self, val=None):
		return float(self.write_or_query("SENS1:FREQ:SPAN", val, "{:e}"))

	def freq_points(self):
		return array(self.instr.query_binary_values( 'CALC:DATA:STIM?', datatype=u'f' ))
		
	def num_of_points(self, val=None):
		return float(self.write_or_query("SENS1:SWE:POIN", int(val), "{:d}"))
		
	def averaging(self, val = None):
		return int(self.write_or_query('SENS:AVER:STAT', self.parse_on_off_val(val), "{:s}"))
		
	def averaging_count(self, val = None):
		return int(self.write_or_query('SENS:AVER:COUN', int(val), '{:d}'))
		

	