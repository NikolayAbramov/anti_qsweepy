from numpy import *
import time
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
from anti_qsweepy.routines.helper_functions import *
	
def BiasSourceByNNDAC(VisaInstrument):

	def __init__(self, *args):
		VisaInstrument.__init__(self, *args, term_chars = '\n')
		self.always_query = True
		self.Vmax = 4.096
		self.ramp_speed = 20. #A/min - current ramp speed
		self.amper_per_volt = 9.847 #A/V	
		
	def setpoint(self, val = None):
		if val is not None:
			V = val/self.amper_per_volt
			V0 = float( self.instrument.query( "volt 0?" ) )
			V1 = float( self.instrument.query( "volt 1?" ) )
			PrevI = (V1-V0)*self.amper_per_volt
			if V < self.Vmax :
				self.instrument.query( "volt 0,0" )
				self.instrument.query( "volt 1,{:e}".format(V) )
			else:
				self.instrument.query( "volt 1,{:e}".format(Vmax) )
				self.instrument.query( "volt 0,{:e}".format( -(V-Vmax) ) )
			wait_time = abs((PrevI-I)/self.ramp_speed*60)+1.
			stupid_waiting(wait_time)
		V0 = float( self.instrument.query( "volt 0?" ) )
		V1 = float( self.instrument.query( "volt 1?" ) )
			#Return actual I set
		return (V1-V0)*self.amper_per_volt
	
	def output(self, val = None):
		pass
	#Voltage limit	
	def limit(self, val=None):
		pass
	
	def range(self, val = None):
		pass
		
	def autorange(self, val=None):
		pass