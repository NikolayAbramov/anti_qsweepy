from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
from anti_qsweepy.drivers.TemperatureControllerBaseClass import *

class TemperatureController(TemperatureControllerBaseClass, VisaInstrument):
	#################################	
	#Temperature setting methods
	def temperature(self, chan):
		buff=self.instr.query("READ:DEV:"+chan+":TEMP:SIG:TEMP")
		strings=buff.split(":")
		Tstring=strings[len(strings)-1]
		Tstring=Tstring[:len(Tstring)-1]
		return float( Tstring )