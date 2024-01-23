from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument

class Voltmeter(VisaInstrument):
	def __init__(self, *args):
		VisaInstrument.__init__(self, *args)
		self.instr.write("*CLS")
		self.instr.write("CONF:VOLT")
		self.instr.write("SENS:CHAN 1")
		self.instr.write( "SENS:VOLT:DFIL:TCON REP" )
		self.instr.write( "SENS:VOLT:DFIL ON" )
		
	def read_data(self):
		return float(self.instr.query("INIT;FETC?"))
			
	def range(self, val=None):
		return float(self.write_or_query("SENS:VOLT:RANG", val, "{:f}"))
		
	def autorange(self, val=None):
		return int(self.write_or_query("SENS:VOLT:RANG:AUTO", self.parse_on_off_val(val), "{:s}"))
	
	def aperture(self, val=None):
		#Voltmeter integration time
		#In this case time units are 50Hz mains cycles
		return int(self.write_or_query("SENS:VOLT:NPLC", val, "{:d}"))

	def averaging_count(self, val=None):
		return int(self.write_or_query("SENS:VOLT:DFIL:COUNT", val, "{:d}"))
		
	#Instrument specific
	def averaging_window(self, val = None):
		#Averaging filter
		return float(self.write_or_query("SENS:VOLT:DFIL:WINDOW", val, "{:f}"))	
	
	#Instrument specific	
	def analog_filter(self, val = None):
		return int(self.write_or_query("SENS:VOLT:LPAS", self.parse_on_off_val(val), "{:s}"))
		
		