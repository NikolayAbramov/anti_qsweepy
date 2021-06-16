from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument

class Voltmeter(VisaInstrument):

	def init(self):
		pass
	
	def wait_done(self):
		pass
		
	def check_done(self):
		return True
		
	def read_data(self):
		return float(self.instr.query("INIT;FETC?"))
			
	def rang(self, val=None):
		return float(self.write_or_query("SENS:VOLT:RANG", val, "{:f}"))
		
	def nplc(self, val=None):
		return float(self.write_or_query("SENS:VOLT:NPLC", val, "{:d}"))
		
	def autorange(self, val=None):
		return int(self.write_or_query("SENS:VOLT:RANG:AUTO", self.parse_on_off_val(val), "{:s}"))
		
	def typical_conf(self, Chan=1, NPLC=1, Range=1, AutoRange="ON"):
		self.instr.write("*CLS")
		self.instr.write("CONF:VOLT")
		self.instr.write("SENS:CHAN {:d}".format(Chan))
		self.instr.write("SENS:VOLT:NPLC {:d}".format(NPLC))
		if AutoRange not in ["ON","OFF"]:
			raise ValueError("Argument AutoRange must be \"ON\" or \"OFF\"")
		if AutoRange == "ON":
			self.instr.write("SENS:VOLT:RANG:AUTO ON")
		elif AutoRange == "OFF":	
			self.instr.write("SENS:VOLT:RANG:AUTO OFF")
			self.instr.write("SENS:VOLT:RANG {:e}".format(Range))	
		
	def filter_conf(Count=1, Window = 3, Type = "REP", Analog = "OFF"):
		#Type: MOV or REP
		self.instr.write( "SENS:VOLT:DFIL:COUNT {:d}".format(Count) )
		self.instr.write( "SENS:VOLT:DFIL:TCON "+Type )
		self.instr.write( "SENS:VOLT:DFIL:WINDOW {:f}".format(Window) )
		self.instr.write( "SENS:VOLT:DFIL:STAT ON" )
		#Analog low pass filter
		if Analog not in ["ON","OFF"]:
			raise ValueError("Argument Analog must be \"ON\" or \"OFF\"")
		if Analog == "ON":
			self.instr.write("SENS:VOLT:LPAS ON")
		elif Analog == "OFF":
			self.instr.write("SENS:VOLT:LPAS OFF")			
		