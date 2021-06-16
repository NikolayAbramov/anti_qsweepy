#Network alnalyzer
from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
import time

class NetworkAnalyzer(VisaInstrument):

	def __init__(self, *args):
		VisaInstrument.__init__(self, *args)
		self.instr.write("CALC:PAR:MNUM 1")
		self.instr.write(':FORMAT REAL,32; FORMat:BORDer SWAP;')
	
	def soft_trig_arm(self):
		self.instr.write("TRIG:SOUR MAN")
		self.instr.write("SENS:AVER:MODE POIN")
		self.instr.write("*ESE 1")	
	
	def read_data(self):
		
		#Clear status, initiate measurement
		self.instr.write("*CLS")
		self.instr.write("INIT:IMM")
		self.instr.write("*OPC")
		#Set bit in ESR when operation complete
		while int(self.instr.query("*ESR?"))==0:
			sleep(0.002)
		
		data = self.instr.query_binary_values("CALC:DATA? SDATA", datatype=u'f') 
		data_size = size(data)
		return array(data[0:data_size:2])+1.j*array(data[1:data_size:2])
	
	def soft_trig_abort(self):
		self.instr.write("TRIG:SOUR IMM")
		
	def power(self, val = None):
		return float(self.write_or_query("SOUR:POW", val, "{:f}"))
	
	def bw(self, val = None):
		return int(self.write_or_query("SENS1:BAND", val, "{:f}"))
		
	def freq_start(self, val=None):
		return float(self.write_or_query("SENS1:FREQ:START", val, "{:e}"))
		
	def freq_stop(self, val=None):
		return float(self.write_or_query("SENS1:FREQ:STOP", val, "{:e}"))
		
	def freq_center(self, val=None):
		return float(self.write_or_query("SENS1:FREQ:CENT", val, "{:e}"))
		
	def freq_span(self, val=None):
		return float(self.write_or_query("SENS1:FREQ:SPAN", val, "{:e}"))	
		
	def num_of_points(self, val=None):
		return float(self.write_or_query("SENS1:SWE:POIN", val, "{:d}"))