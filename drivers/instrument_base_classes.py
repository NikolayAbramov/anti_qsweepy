import pyvisa as visa

#Base class for VISA instruments that use SCPI-style syntax
class VisaInstrument():
	def __init__(self, address, term_chars = None):
		self.instr = visa.ResourceManager().open_resource(address)
		self.always_query = False
		if term_chars is not None:
			self.instr.read_termination = term_chars
			self.instr.weite_termination = term_chars
	
	#Uneversal parameter access. If no val specified it will query and return or write instead
	def write_or_query(self, message, val=None, fmt_str = "{:d}"):
		if val is not None:
			if self.always_query:
				val = self.instr.query(message+" "+fmt_str.format(val))
			else:	
				self.instr.write(message+" "+fmt_str.format(val))
			return val
		else:
			return self.instr.query(message+"?")
			
	def parse_on_off_val(self, val):
		if val is not None:
			if val not in ["on","off","ON","OFF","1","0",1,0]:
				raise ValueError("Argument must be either of [\"ON\",\"OFF\",\"1\",\"0\",1,0]")
			if val in [1,0]: 
				val = str(val)
			elif val.upper() == "ON":
				val = "1"
			else:
				val = "0"
		return val
		
	#Standard SCPI commands
	#Query instrument id string		
	def idn(self):
		return self.instr.query("*IDN?")
		
#Base class for VISA instruments that use
#Test Script Processor (TSP) inscead of normal SCPI syntax		
class VisaInstrumentTSP(VisaInstrument):
	
	#Uneversal parameter access. If no val specified it will query and return or write value instead.
	def write_or_query(self, message, val=None, fmt_str = "{:d}"):
		if val is not None:
			self.instr.write( message+" = "+fmt_str.format(val) )
			return val
		else:
			return self.instr.query( 'print({:s})'.format(message) )	