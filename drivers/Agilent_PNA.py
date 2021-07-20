#Network alnalyzer
from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
import time

class NetworkAnalyzer(VisaInstrument):

	def __init__(self, *args):
		VisaInstrument.__init__(self, *args)
		self.instr.write("CALC:PAR:MNUM 1")
		self.instr.write('FORM REAL,32; FORM:BORD SWAP;')
	
	def soft_trig_arm(self):
		self.instr.write("TRIG:SOUR MAN")
		self.instr.write("SENS:AVER:MODE POIN")
		self.instr.write("*ESE 1")	
	
	def read_data(self):
		#Clear status, initiate measurement
		self.instr.write("*CLS")
		self.instr.write("INIT:IMM")
		self.instr.write("*OPC")
		#Set bit in ESR when operation complete
		while int(self.instr.query("*ESR?"))==0:
			time.sleep(0.002)
		data = self.instr.query_binary_values("CALC:DATA? SDATA", datatype=u'f') 
		data_size = size(data)
		return array(data[0:data_size:2])+1.j*array(data[1:data_size:2])
	
	def soft_trig_abort(self):
		self.instr.write("TRIG:SOUR IMM")
		
	def power(self, val = None):
		return float(self.write_or_query("SOUR:POW", val, "{:f}"))
	
	def bandwidth(self, val = None):
		return int(self.write_or_query("SENS1:BAND", val, "{:f}"))
		
	def freq_start(self, val=None):
		return float(self.write_or_query("SENS1:FREQ:START", val, "{:e}"))
		
	def freq_stop(self, val=None):
		return float(self.write_or_query("SENS1:FREQ:STOP", val, "{:e}"))
		
	def freq_center(self, val=None):
		return float(self.write_or_query("SENS1:FREQ:CENT", val, "{:e}"))
		
	def freq_span(self, val=None):
		return float(self.write_or_query("SENS1:FREQ:SPAN", val, "{:e}"))	
		
	def num_of_points(self, val=None):
		return int(self.write_or_query("SENS1:SWE:POIN", val, "{:d}"))
		
	def output(self, val=None):
		return(self.write_or_query( 'OUTP', self.parse_on_off_val(val), "{:s}" ) )
		
	def freq_points(self):
		#start = self.freq_start()
		#stop = self.freq_stop()
		#nop = self.num_of_points()
		#return linspace(start,stop,nop)
		return array(self.instr.query_binary_values( 'SENS1:X?', datatype=u'f' ))
		
	def	sweep_type(self, val = None):
		if val is not None:
			val = val.upper()
			if val.upper() not in ['SEGM','LIN','CW','POW','LOG']:
				raise ValueError("Argument must be either of [\"SEGM\",\"LIN\",\"CW]")
		return self.write_or_query("SENS1:SWE:TYPE", val, "{:s}")
		
	def seg_tab(self, seg_tab):
		#Segment description format:
		#{'start':0, 'stop':0, 'points':0, 'power':0,'bandwidth':0}	
		#SegTable = '{:d}'.format(len(seg_tab))
		
		#for seg in seg_tab:
		#	SegTable += ',1,{:d}'.format( int(seg['points'] ) )	
		#	SegTable += ',{:e},{:e},{:e}'.format( seg['start'], seg['stop'], seg['Bandwidth'] )
		
		self.instr.write("SENS1:SEGM:DEL:ALL")
		self.instr.write("SENS1:SEGM:BWID:CONT ON")
		self.instr.write("SENS1:SEGM:POW:CONT ON")
		for i,seg in enumerate(seg_tab):
			n=i+1
			self.instr.write("SENS1:SEGM{:d}:ADD".format(n))
			self.instr.write("SENS:SEGM{:d}:BWID {:f}".format(n,seg['bandwidth']) )
			self.instr.write("SENS:SEGM{:d}:POW {:f}".format(n,seg['power']) )
			self.instr.write("SENS:SEGM{:d}:FREQ:START {:f}".format(n,seg['start']) )
			self.instr.write("SENS:SEGM{:d}:FREQ:STOP {:f}".format(n,seg['stop']) )
			self.instr.write("SENS:SEGM{:d}:SWE:POIN {:d}".format(n,seg['points']) )
			self.instr.write("SENS:SEGM{:d} ON".format(n))
		#self.instr.write("SENS1:SEGM:LIST SSTOP,"+SegTable)
		
		