import numpy as np
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
import ctypes

class SpectrumAnalyzer(VisaInstrument):
	"""This is the python driver for the Signal Hound SA124 spectrum analyzer"""
	def __init__(self, *args):
		"""
		Initializes 

		Input:
			serial (int) : serial number
		"""
		VisaInstrument.__init__(self, *args)
		#Set detector type "Average"
		self.instr.write(':DET:TRAC SAMP')
		
	def soft_trig_arm(self):
		self.instr.write(':INIT:CONT OFF')
		pass

	def soft_trig_abort(self):
		self.instr.write(':INIT:CONT ON')
		pass	
	
	def read_data(self):
		"""Returns measured spectrum in watts"""
		
		self.instr.query(':INIT:IMM;*OPC?')
		buffer = self.instr.query("CALC:DATA?")
		data = np.fromstring(buffer, sep = ",", dtype = np.float)
		S = data[1::2]
		F = data[0::2]
		S = 10**(S/10)*1e-3
		return S
		
	def rbw(self, val = None):
		'''
		Resolution bandwidth
		'''
		if val is not None:
			self.instr.write(":BAND {:e}".format(val))
		else:
			val = float(self.instr.query(":BAND?"))
		return  val
	
	def vbw(self, val = None):
		'''
		Video bandwidth
		'''
		if val is not None:
			self.instr.write(":BAND:VID {:e}".format(val))
		else:
			val = float(self.instr.query(":BAND:VID?"))
		return  val
	
	def ref_level(self, val = None):
		if val is not None:
			self.instr.write(":DISP:WIND:TRAC:Y:RLEV {:e}".format(val[0]))
		else:
			val = float(self.instr.query(":DISP:WIND:TRAC:Y:RLEV?"))
		return  val
		
	def freq_start_stop(self, val = None):
		if val is not None:
			self.instr.write(":FREQ:STAR {:e}".format(val[0]))
			self.instr.write(":FREQ:STOP {:e}".format(val[1]))
		else:
			val = [0,0]
			val[0] = float(self.instr.query(":FREQ:STAR?"))
			val[1] = float(self.instr.query(":FREQ:STOP?"))
		return val	
	
	def freq_center_span(self, val = None):
		if val is not None:
			self.instr.write(":FREQ:CENT {:e}".format(val[0]))
			self.instr.write(":FREQ:SPAN {:e}".format(val[1]))
		else:
			val = [0,0]
			val[0] = float(self.instr.query(":FREQ:CENT?"))
			val[1] = float(self.instr.query(":FREQ:SPAN?"))
		return val	

	def freq_points(self):
		buffer = self.instr.query("CALC:DATA?")
		data = np.fromstring(buffer, sep = ",", dtype = np.float)
		F = data[0::2]
		return F
		
	def averaging(self, val = None):
		#Not supported
		return 1