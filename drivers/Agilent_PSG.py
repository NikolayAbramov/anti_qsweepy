#RF generator
from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
import time

class Generator(VisaInstrument):

	def __init__(self, *args):
		VisaInstrument.__init__(self, *args)
	
	def power(self, val = None):
		return float(self.write_or_query("POW", val, "{:f}"))
		
	def freq(self, val=None):
		return float(self.write_or_query("FREQ", val, "{:e}"))
		
	def phase(self, val=None):
		return float(self.write_or_query("PHASE", val, "{:e}"))
		
	def output(self, val=None):
		return(self.write_or_query( 'OUTP', self.parse_on_off_val(val), "{:s}" ) )