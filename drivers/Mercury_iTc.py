from numpy import *
from anti_qsweepy.routines.helper_functions import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
import time

#Mercury iTC temperature controller
class PIDtable:
	def __init__(self):
		self.Auto = False
		#PID table format Tstart Tstop P I D V
		self.Table = np.array([])

class Mercury_iTc(VisaInstrument):
	def __init__(self, *args):
		VisaInstrument.__init__(self, *args)
		self.timeout = 10.
		self.PIDfileDefaultPath = 'C:\\Users\\Public\\Documents\\iTC PID tables'
		self.AutoPID = False
		self.PIDtables = {}
	###############################	
	#PID tables handling	
	def SetPIDtable(self, Chan, PIDFile):
		val,err = self.GetLoopParam( Chan, "PIDT")
		if not(err):
			Pt = PIDtable()
			Pt.Table = np.loadtxt( self.PIDfileDefaultPath+'\\'+PIDFile )
			self.PIDtables[Chan] = Pt
			Status = True
		else: Status = False	
		return Status
	
	def SetAutoPID(self, Chan, Mode):
		#Mode True or False
		if Chan in self.PIDtables.keys():
			self.PIDtables[Chan].Auto = Mode
			self.SetLoopParam( Chan, "PIDT", "OFF")
			Status = True
		else: 
			print("iTC: No PID table for {:s} channel".format(Chan))
			Status = False
		return Status
		
	def RemovePIDtable(self, Chan):
		if Chan in self.PIDtables.keys():
			self.PIDtables.pop(Chan)
			Status = True
		else: 
			print("iTC: No PID table for {:s} channel".format(Chan))
			Status = False
		return Status
		
	def ClearPIDtables(self):	
		self.PIDtables.clear()
	
	def SetPIDV(self, Chan, Tset):
		if Chan in self.PIDtables.keys():
			Table = self.PIDtables[Chan].Table
			for i in range(0,len(Table)):
				if (Tset < Table[i][0]):
					if not(i==0): PIDV = Table[i-1][1:]
					else: PIDV = Table[i][1:]
					break
				if (Tset >= Table[i][0]) and (i == len(Table)-1):
					PIDV = Table[i][1:]
			if not(PIDV[0] == self.GetLoopParam( Chan, "P" )[0]):	
				self.SetLoopParam( Chan, "P", PIDV[0])
			if not(PIDV[1] == self.GetLoopParam( Chan, "I" )[0]):	
				self.SetLoopParam( Chan, "I", PIDV[1])
			if not(PIDV[2] == self.GetLoopParam( Chan, "D" )[0]):	
				self.SetLoopParam( Chan, "D", PIDV[2])
			
			Heater = self.GetLoopParam( Chan,"HTR" )[0]
			if not(PIDV[3] == self.GetHeaterParam( Heater, "VLIM" )[0]):	
				self.SetHeaterParam( Heater, "VLIM", PIDV[3])
			Status = True
		else: 
			print("iTC: No PID table for {:s} channel".format(Chan))
			Status = False
		return Status

	#################################	
	#Temperature setting methods
	def setpoint(self,chan,setpoint):
		if Chan in self.PIDtables.keys():
			if self.PIDtables[Chan].Auto:
				self.SetPIDV( Chan, Setpoint )
		self.SetLoopParam(Chan,"TSET",Setpoint)
	
	def heater_value(self, chan):
		(Hset,err) = self.GetLoopParam(Chan,"HSET")
		return Hset	
		
	def temperature(self, chan):
		(T,err) = self.GetSensorSig(Chan,"TEMP")
		return T
	
	def SwitchHtrRange(self, Heater, Tset, HtrRangeList):
		i_stop = len(HtrRangeList)-1
		for i in range(0,i_stop+1):
			if ( Tset > HtrRangeList[i][0] ) or (Tset == HtrRangeList[i][0] ):
				if i == i_stop:
					Vlim = HtrRangeList[i][1]
					break
				if Tset < HtrRangeList[i+1][0]:
					Vlim = HtrRangeList[i][1]
					break
		if not(Vlim == self.GetHeaterParam( Heater, "VLIM" )[0]):	
			self.SetHeaterParam( Heater, "VLIM", Vlim)
	
	def GetSensorSig(self, Sens, Param ):
		#Param = VOLT,CURR,POWR,RES,TEMP,SLOP
		String = self.ask("READ:DEV:"+Sens+":TEMP:SIG:"+Param)
		if self.ErrChk(String):
			err = False
			val = self.ExtractAns(String, True)
		else: 
			val = 0.0
			err = True
		return val,err	
	#Get heater power
	def GetP(self, Heater):
		String = self.ask("READ:DEV:"+Heater+":HTR:SIG:POWR")
		if self.ErrChk(String):
			err = False
			P = self.ExtractAns(String, True)
		else: 
			P=0.
			err = True	
		return P,err	
	
	def SetHeaterParam(self, Heater, Param, Value):
		#Param = NICK,VLIM,RES
		ValStr = ""
		if type(Value)==str: 
			ValStr = Value
		else: 
			ValStr = "{:f}".format(Value)
		
		ans = self.ask( "SET:DEV:"+Heater+":HTR:"+Param+":"+ValStr )
		return self.ErrChk(ans)

	def GetHeaterParam(self, Heater, Param):
		#Param = NICK,VLIM,RES,PMAX
		ans = self.ask( "READ:DEV:"+Heater+":HTR:"+Param )
		if Param in ["NICK"]:
			if self.ErrChk(ans): 
				err = False
				val = self.ExtractAns(ans, False)
			else: val = ""
		else: 
			if self.ErrChk(ans): 
				err = False
				val = self.ExtractAns(ans, True)
			else: 
				val = 0.
				err = True
		return val,err
	
	def SetHeaterSig(self, Heater, Sig, Value):
	#Sig = VOLT,CURR,POWR
		ans = self.ask( "SET:DEV:"+Heater+":HTR:SIG:"+Sig)
		return not( self.ErrChk(ans) )
	
	def GetLoopParam(self, Loop, Param):
		#Param = HTR,AUX,ENAB,HSET,TSET,PIDT,PSET,ISET,DSET,SWFL,SWMD
		ans = self.ask( "READ:DEV:"+Loop+":TEMP:LOOP:"+Param )
		if Param in ["HTR", "ENAB","PIDT","SWMD"]:
			if self.ErrChk(ans): 
				err = False
				val = self.ExtractAns(ans, False)
			else: 
				val = ""
				err = True
		else: 
			if self.ErrChk(ans): 
				err = False
				val = self.ExtractAns(ans, True)
			else: 
				val = 0.
				err = True
		return val,err
	
	def SetLoopParam(self, Loop, Param, Value):
		#Param = HTR,AUX,ENAB,HSET,TSET,PIDT,PSET,ISET,DSET,SWFL,SWMD
		ValStr = ""
		if type(Value) == str: 
			ValStr = Value
		else: 
			ValStr = "{:f}".format(Value)
		ans = self.ask( "SET:DEV:"+Loop+":TEMP:LOOP:"+Param+":"+ValStr )	
		return self.ErrChk(ans)
	
	def shutdown(self, Sensor):
		self.SetLoopParam( Sensor,"SWMD", "FIX" )		
		self.SetLoopParam( Sensor,"TSET",0. )
		self.SetLoopParam( Sensor,"ENAB","OFF" )
		self.SetLoopParam( Sensor,"HSET",0.)
		
	def RunSweep(self, Loop, Sweep):
		self.SetLoopParam( Loop,"SWFL", Sweep )
		self.SetLoopParam( Loop,"SWMD", "SWP" )
	
	def ExtractAns(self, String, IsNumber):
		list = String.split(':')
		if IsNumber == True:
			val = float( list[-1].strip(string.ascii_uppercase) )
			return val
		else: return list[-1]
	
	def ErrChk(self, String):
		Status = True
		ans = String.split(":")[-1]
		if ans=="INVALID" or ans=="N/A" or ans=="NOT_FOUND" or ans=="DENIED" or ans == "":
			print("iTC: Error: "+String)
			Status = False
		return Status
		
'''	
class TemperatureController():
	
	def setp(self,chan, val = None):
	
	def temperature(self, chan):
	
	def ramp(self, chan, mode, rate=None):
	
		iTc.SetLoopParam( chan,"SWFL", Sweep )
		iTc.SetLoopParam( chan,"SWMD", "SWP" )
	
	#mode ON OFF
	
	def load_zones(self, chan):
	
	def heater_range(self, chan, val = None):

	def heater_value(self, chan, val = None):
	
	def heater_mode(self, chan, mode):
'''	