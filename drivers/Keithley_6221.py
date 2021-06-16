from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument

class CurrentSource(VisaInstrument):
		
	def current(self, val = None):
		return float(self.write_or_query("SOUR:CURR", val, "{:f}"))
	
	def output(self, val = None):
		return int(self.write_or_query("OUTP:STAT", self.parse_on_off_val(val), "{:s}"))
		
	def compliance(self, val=None):
		return float(self.write_or_query("SOUR:CURR:COMP", val, "{:f}"))
	
	def rang(self, val = None):
		return float(self.write_or_query("SOUR:CURR:RANG", val, "{:f}"))
		
	def autorange(self, val=None):
		return int(self.write_or_query("SOUR:CURR:RANG:AUTO", self.parse_on_off_val(val), "{:s}"))
		
	def filter(self, val=None):
		return int(self.write_or_query("SOUR:CURR:FILT", self.parse_on_off_val(val), "{:s}"))	
		
	#A typical one shoot measurement configuration
	def typical_conf(self, autorange = "ON", rang = 1.05e-3, grounded = "ON", compliance = 1):
		#Inner shield is "output low"
		self.instr.write("OUTP:ISH OLOW")
		#Output low can be connected to the chassis if "ON"
		self.instr.write("OUTP:LTE " + grounded)
		self.compliance(compliance)
		self.autorange(autorange)
		self.rang(rang)
		self.filter("ON")
		self.current(0)