from numpy import *
import time
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrumentTSP

class CurrentSource(VisaInstrumentTSP):

	def __init__(self, *args):
		VisaInstrumentTSP.__init__(self, *args)
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
		
class MagnetSupply(CurrentSource):

	def __init__(self, *args):
		CurrentSource.__init__(self, *args)
		self.i_step = 0.05
		self.rate = 0.1
		
	def setpoint(self, val = None):
		if val is not None:
			self._slow_i(val)
		else:	
			return float( self.instr.query("print(smua.source.leveli)") )
			
	def _slow_i(self,I):
		Icurr = float( self.instr.query("print(smua.source.leveli)") )
		dI = I - Icurr
		if abs(dI)>self.i_step*2:
			for I in linspace(Icurr, I, int(abs(dI)/self.i_step)):
				self.instr.write( "smua.source.leveli = {:e}".format(I) )
				time.sleep(self.rate)
		else:
			self.instr.write( "smua.source.leveli = {:e}".format(I) )