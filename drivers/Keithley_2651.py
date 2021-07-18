from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrumentTSP

class CurrentSource(VisaInstrumentTSP):

	def __init__(self, *args):
		VisaInstrument.__init__(self, *args)
		self.instr.write('smua.source.func = smua.OUTPUT_DCAMPS')
		
	def setpoint(self, val = None):
		return float(self.write_or_query("smua.source.leveli", val, "{:e}"))
	
	def output(self, val = None):
		return int(self.write_or_query("smua.source.output", self.parse_on_off_val(val), "{:s}"))
	#Voltage limit	
	def limit(self, val=None):
		return float(self.write_or_query("smua.source.limitv", val, "{:e}"))
	
	def range(self, val = None):
		return float(self.write_or_query("smua.source.rangei", val, "{:e}"))
		
	def autorange(self, val=None):
		return int(self.write_or_query("smua.source.autorangei", self.parse_on_off_val(val), "{:s}"))