from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument

class SMU(VisaInstrument):

	def __init__(self, *args, **kwargs):
		VisaInstrument.__init__(self, *args, **kwargs)
		self.data_ind = 0
		self.measurement_type = "VOLT"
		self.source_type = self.source()
		self.instr.write("AVER:TCON:REP")
	
	def four_wire(self, val = None):
		#On - 4-wire, Off - 2-wire
		return int(self.write_or_query("SYST:RSEN", self.parse_on_off_val(val), "{:s}"))	
		
	def source(self, val = None):
		#current, voltage
		if val is not None:
			val = val.upper()
			if val not in ['CURRENT', 'VOLTAGE']:
				raise ValueError("Source must be Current or Voltage!")
		val = self.write_or_query('SOUR:FUNC', val, '{:s}')
		if val[-1] == '\n':
			val = val[:-1]
		val = val.upper()	
		self.source_type = val
		if val.find("VOLT") != -1:
			self.measurement_type = "CURR"
			self.data_ind = 1
		else:	
			self.measurement_type = "VOLT"
			self.data_ind = 0
		return val
		
	def output(self, val = None):
		return int(self.write_or_query("OUTP", self.parse_on_off_val(val), "{:s}"))	
		
	def setpoint(self, val = None):
		return float( self.write_or_query('SOUR:'+self.source_type, val, "{:e}") )
	
	def read_data(self):
		return float(self.instr.query('MEAS:'+self.measurement_type+'?').split(',')[self.data_ind])
		
	def limit(self, val=None):
		return float(self.write_or_query( self.measurement_type+':PROT', val, "{:e}"))
	
	def source_range(self, val = None):
		return float( self.write_or_query('SOUR:'+self.source_type+':RANG', val, "{:e}") )
		
	def measurement_range(self, val = None):
		return float( self.write_or_query(self.measurement_type+':RANG', val, "{:e}") )	
		
	def source_autorange(self, val=None):
		return int(self.write_or_query('SOUR:'+self.source_type+':RANG:AUTO', self.parse_on_off_val(val), "{:s}"))
		
	def measurement_autorange(self, val=None):
		return int(self.write_or_query(self.measurement_type+':RANG:AUTO', self.parse_on_off_val(val), "{:s}"))	
		
	def aperture(self, val = None):
		return int(self.write_or_query( self.measurement_type+':NPLC', val, "{:d}"))
	
	def averaging_count(self, val=None):
		return int(self.write_or_query("AVER:COUNT", val, "{:d}"))	
		
	def preset(self):
		self.instr.write('SYST:PRES')
		
class CurrentSource(VisaInstrument):
	def __init__(self, *args, **kwargs):
		VisaInstrument.__init__(self, *args, **kwargs)
		self.instr.write('SOUR:FUNC:CURR')
	
	def setpoint(self, val = None):
		return float( self.write_or_query('SOUR:CURR', val, "{:e}") )
	
	def output(self, val = None):
		return int(self.write_or_query("OUTP", self.parse_on_off_val(val), "{:s}"))
		
	def limit(self, val=None):
		return float(self.write_or_query( 'VOLT:PROT', val, "{:e}"))
	
	def range(self, val = None):
		return float( self.write_or_query('SOUR:CURR:RANG', val, "{:e}") )
		
	def autorange(self, val=None):
		return int(self.write_or_query('SOUR:CURR:RANG:AUTO', self.parse_on_off_val(val), "{:s}"))