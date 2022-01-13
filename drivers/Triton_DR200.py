from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
from anti_qsweepy.drivers.TemperatureControllerBaseClass import *

class TemperatureController(TemperatureControllerBaseClass, VisaInstrument):
	def __init__(self, *args, **kwargs):
		VisaInstrument.__init__(self, *args, term_chars = "\n", **kwargs)
	#################################	
	#Temperature setting methods
	def temperature(self, chan):
		buff=self.instr.query("READ:DEV:"+chan+":TEMP:SIG:TEMP")
		strings=buff.split(":")
		Tstring=strings[len(strings)-1]
		Tstring=Tstring[:len(Tstring)-1]
		return float( Tstring )
		
class Cryostat(VisaInstrument):
	def __init__(self, *args, **kwargs):
		VisaInstrument.__init__(self, *args, term_chars = "\n", **kwargs)
		self.mc_sensor_low = 5
		self.mc_sensor_high = 6
		self.Tmc_thr = 1.45
	#################################	
	#Read temperature
	def _get_response(self, buff):
		strings = buff.split(":")
		return strings[len(strings)-1]
		
	def temperature(self, chan):
		buff=self.instr.query("READ:DEV:T{:d}:TEMP:SIG:TEMP".format(chan))
		strings=buff.split(":")
		Tstring=strings[len(strings)-1]
		Tstring=Tstring[:len(Tstring)-1]
		return float( Tstring )
		
	def Tmc(self):
		T = self.temperature(self.mc_sensor_low)
		if T >= self.Tmc_thr:
			T = self.temperature(self.mc_sensor_high)
		return T	

	def sensor(self, chan, state = None):
		if chan<1 or chan>6:
			raise ValueError('Invalid sensor ID')
		if state is not None:
			if state<0:
				raise ValueError('Invalid state')
			if state:
				state_str = 'ON'
				state = 1
			else:
				state_str = 'OFF'
			self.instr.query('SET:DEV:T{:d}:TEMP:MEAS:ENAB:{:s}'.format(chan, state_str))
		else:
			ans = self.instr.query('READ:DEV:T{:d}:TEMP:MEAS:ENAB'.format(chan))
			ans = self._get_response(ans)
			if ans == 'ON':
				state = 1
			elif ans == 'OFF':
				state = 0
		return state

	def valve(self, chan, state = None):
		if chan<1 or chan>9:
			raise ValueError('Invalid valve ID')	
		if state is not None:
			if state<0:
				raise ValueError('Invalid state')
			if state:
				state_str = 'OPEN'
				state = 1
			else:
				state_str = 'CLOSE'
			self.instr.query('SET:DEV:V{:d}:VALV:SIG:STATE:{:s}'.format(chan, state_str))
		else:
			ans = self.instr.query('READ:DEV:V{:d}:VALV:SIG:STATE'.format(chan))
			ans = self._get_response(ans)
			if ans == 'OPEN':
				state = 1
			elif ans == 'CLOSE':
				state = 0
		return state
		
	def pressure(self, chan):
		#Returns pressure in mbar
		if chan<1 or chan>5:
			raise ValueError('Invalid pressure gauge ID')
		ans = self.instr.query('READ:DEV:P{:d}:PRES:SIG:PRES'.format(chan))
		ans = self._get_response(ans)
		p = float(ans[:-2])
		return p

	def turbo_status(self):
		#Returns turbo pump status
		#state 1/0
		#power W
		#speed Hz
		ans = self.instr.query('READ:DEV:TURB1:PUMP:SIG:STATE')
		ans = self._get_response(ans)
		if ans == "ON":
			state = 1
		elif ans == 'OFF':
			state = 0
		else:
			raise Exception(str)
		ans = self.instr.query('READ:DEV:TURB1:PUMP:SIG:POWR')
		ans = self._get_response(ans)
		power = float(ans[:-1])
		ans = self.instr.query('READ:DEV:TURB1:PUMP:SIG:SPD')
		ans = self._get_response(ans)
		speed = float(ans[:-2])
		return {'state':state, 'power':power, 'speed':speed}
	
	def _pump(self, pump, state = None):
		if state is not None:
			if state<0: raise ValueError('Invalid state')
			if state:
				state_str = 'ON'
				state = 1
			else:
				state_str = 'OFF'
			self.instr.query('SET:DEV:'+pump+':PUMP:SIG:STATE:'+state_str)
		else:
			ans = self.instr.query('READ:DEV:'+pump+':PUMP:SIG:STATE')
			ans = self._get_response(ans)
			if ans == "ON": state = 1
			elif ans == 'OFF': state = 0
			else: raise Exception(ans)
		return state
		
	def turbo(self, state = None):
		return self._pump('TURB1', state)

	def forepump(self, state = None):
		return self._pump('FP', state)
		
	def compressor(self, state = None):
		return self._pump('COMP', state)
		
	def _heater(self, heater, power = None):
		#Power in uW
		if power is not None:
			if power<0.: raise ValueError('Invalid power')
			self.instr.query('SET:DEV:'+heater+':HTR:SIG:POWR:{:e}'.format(power))
		else:
			ans = self.instr.query('READ:DEV:'+heater+':HTR:SIG:POWR')
			ans = self._get_response(ans)
			power = float(ans[:-2])
		return power	
	
	def chamber_heater(self, power = None):
		return self._heater('H1', power)
		
	def still_heater(self, power = None):
		return self._heater('H2', power)
		
	def stop_automation(self):
		self.instr.query('SET:SYS:DR:ACTN:STOP')
		
	def start_condensing(self):
		self.instr.query('SET:SYS:DR:ACTN:COND')