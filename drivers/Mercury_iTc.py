from numpy import *
from anti_qsweepy.routines.helper_functions import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
from anti_qsweepy.drivers.TemperatureControllerBaseClass import *
import time
import string


# Mercury iTC temperature controller
class PIDtable:
    def __init__(self):
        self.Auto = False
        # PID table format Tstart Tstop P I D V
        self.Table = array([])


class TemperatureController(TemperatureControllerBaseClass, VisaInstrument):
    def __init__(self, *args, **kwargs):
        VisaInstrument.__init__(self, *args, term_chars='\n', **kwargs)
        self.timeout = 10.
        self.AutoPID = False
        self.PIDtables = {}

    ###############################
    # PID tables handling

    #################################
    # Temperature setting methods
    def temperature(self, chan):
        (T, err) = self.GetSensorSig(chan, "TEMP")
        return T

    def setpoint(self, chan, val=None):
        if val is not None:
            if chan in self.PIDtables.keys():
                if self.PIDtables[chan].Auto:
                    self.SetPIDV(chan, val)
            self.SetLoopParam(chan, "TSET", val)
        else:
            val, err = self.GetLoopParam(chan, "TSET")
        return val

    def heater_value(self, chan, val=None):
        if val is not None:
            self.SetLoopParam(chan, "HSET", val)
        else:
            val, err = self.GetLoopParam(chan, "HSET")
        return val

    def heater_range(self, chan, val=None):
        if val is not None:
            self.SetHeaterParam(chan, "VLIM", val)
        else:
            val, err = self.GetHeaterParam(chan, "VLIM")
        return val

    ###############
    def SetPIDtable(self, Chan, PIDFile):
        val, err = self.GetLoopParam(Chan, "PIDT")
        if not (err):
            Pt = PIDtable()
            Pt.Table = loadtxt(PIDFile)
            self.PIDtables[Chan] = Pt
            Status = True
        else:
            Status = False
        return Status

    def SetAutoPID(self, Chan, Mode):
        # Mode True or False
        if Chan in self.PIDtables.keys():
            self.PIDtables[Chan].Auto = Mode
            self.SetLoopParam(Chan, "PIDT", "OFF")
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
            for i in range(0, len(Table)):
                if (Tset < Table[i][0]):
                    if not (i == 0):
                        PIDV = Table[i - 1][1:]
                    else:
                        PIDV = Table[i][1:]
                    break
                if (Tset >= Table[i][0]) and (i == len(Table) - 1):
                    PIDV = Table[i][1:]
            if not (PIDV[0] == self.GetLoopParam(Chan, "P")[0]):
                self.SetLoopParam(Chan, "P", PIDV[0])
            if not (PIDV[1] == self.GetLoopParam(Chan, "I")[0]):
                self.SetLoopParam(Chan, "I", PIDV[1])
            if not (PIDV[2] == self.GetLoopParam(Chan, "D")[0]):
                self.SetLoopParam(Chan, "D", PIDV[2])

            Heater = self.GetLoopParam(Chan, "HTR")[0]
            if not (PIDV[3] == self.GetHeaterParam(Heater, "VLIM")[0]):
                self.SetHeaterParam(Heater, "VLIM", PIDV[3])
            Status = True
        else:
            print("iTC: No PID table for {:s} channel".format(Chan))
            Status = False
        return Status

    def SwitchHtrRange(self, Heater, Tset, HtrRangeList):
        i_stop = len(HtrRangeList) - 1
        for i in range(0, i_stop + 1):
            if (Tset > HtrRangeList[i][0]) or (Tset == HtrRangeList[i][0]):
                if i == i_stop:
                    Vlim = HtrRangeList[i][1]
                    break
                if Tset < HtrRangeList[i + 1][0]:
                    Vlim = HtrRangeList[i][1]
                    break
        if not (Vlim == self.GetHeaterParam(Heater, "VLIM")[0]):
            self.SetHeaterParam(Heater, "VLIM", Vlim)

    def GetSensorSig(self, Sens, Param):
        # Param = VOLT,CURR,POWR,RES,TEMP,SLOP
        String = self.instr.query("READ:DEV:" + Sens + ":TEMP:SIG:" + Param)
        if self.ErrChk(String):
            err = False
            val = self.ExtractAns(String, True)
        else:
            val = 0.0
            err = True
        return val, err

    # Get heater power
    def GetP(self, Heater):
        String = self.instr.query("READ:DEV:" + Heater + ":HTR:SIG:POWR")
        if self.ErrChk(String):
            err = False
            P = self.ExtractAns(String, True)
        else:
            P = 0.
            err = True
        return P, err

    def SetHeaterParam(self, Heater, Param, Value):
        # Param = NICK,VLIM,RES
        ValStr = ""
        if type(Value) == str:
            ValStr = Value
        else:
            ValStr = "{:f}".format(Value)

        ans = self.instr.query("SET:DEV:" + Heater + ":HTR:" + Param + ":" + ValStr)
        return self.ErrChk(ans)

    def GetHeaterParam(self, Heater, Param):
        # Param = NICK,VLIM,RES,PMAX
        ans = self.instr.query("READ:DEV:" + Heater + ":HTR:" + Param)
        if Param in ["NICK"]:
            if self.ErrChk(ans):
                err = False
                val = self.ExtractAns(ans, False)
            else:
                val = ""
        else:
            if self.ErrChk(ans):
                err = False
                val = self.ExtractAns(ans, True)
            else:
                val = 0.
                err = True
        return val, err

    def SetHeaterSig(self, Heater, Sig, Value):
        # Sig = VOLT,CURR,POWR
        ans = self.instr.query("SET:DEV:" + Heater + ":HTR:SIG:" + Sig)
        return not (self.ErrChk(ans))

    def GetLoopParam(self, Loop, Param):
        # Param = HTR,AUX,ENAB,HSET,TSET,PIDT,PSET,ISET,DSET,SWFL,SWMD
        ans = self.instr.query("READ:DEV:" + Loop + ":TEMP:LOOP:" + Param)
        if Param in ["HTR", "ENAB", "PIDT", "SWMD"]:
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
        return val, err

    def SetLoopParam(self, Loop, Param, Value):
        # Param = HTR,AUX,ENAB,HSET,TSET,PIDT,PSET,ISET,DSET,SWFL,SWMD
        ValStr = ""
        if type(Value) == str:
            ValStr = Value
        else:
            ValStr = "{:f}".format(Value)
        ans = self.instr.query("SET:DEV:" + Loop + ":TEMP:LOOP:" + Param + ":" + ValStr)
        return self.ErrChk(ans)

    def shutdown(self, Sensor):
        self.SetLoopParam(Sensor, "SWMD", "FIX")
        self.SetLoopParam(Sensor, "TSET", 0.)
        self.SetLoopParam(Sensor, "ENAB", "OFF")
        self.SetLoopParam(Sensor, "HSET", 0.)

    def RunSweep(self, Loop, Sweep):
        self.SetLoopParam(Loop, "SWFL", Sweep)
        self.SetLoopParam(Loop, "SWMD", "SWP")

    def ExtractAns(self, str, IsNumber):
        list = str.split(':')
        if IsNumber == True:
            val = float(list[-1].strip(string.ascii_uppercase))
            return val
        else:
            return list[-1]

    def ErrChk(self, String):
        Status = True
        ans = String.split(":")[-1]
        if ans == "INVALID" or ans == "N/A" or ans == "NOT_FOUND" or ans == "DENIED" or ans == "":
            print("iTC: Error: " + String)
            Status = False
        return Status
