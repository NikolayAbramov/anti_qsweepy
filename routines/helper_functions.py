import time
from numpy import *

def set_slow(val, speed, func, delay = 0.1):
	actual = func()
	delta = val - actual
	step = speed*delay
	if abs(delta)> step*2:
		for set_val in linspace( actual, val,  int( abs(delta)/step ) ):
			func( set_val )
			time.sleep( delay )
	else:		
		func( val )
		
def WaitForStableT(T_getter, Sensor, Tolerance, HoldTime, H_getter = None, Timeout = 600., Interval = 2.):
		StartTime = time.time()
		RefTime = StartTime
		InTol = False
		Status  = False
		T = T_getter(Sensor)
		Tref = T
		while(1):
			T = T_getter(Sensor)
			if H_getter is not None:
				H = H_getter(Sensor)
			Time = time.time()
			if H_getter is not None:
				print("Waiting for setpoint {:.4f}K, T={:.4f}K, heater {:.2f}%".format(Setpoint,T,H), end='\r')
			else:	
				print(" Waiting for stable temperature, T={:.4f}K".format(T), end = '\r')	
			if (T<=(Tref+Tolerance)) and (T>=(Tref-Tolerance)):
				if (Time-RefTime) >= HoldTime:
					Status = True
					break
			else:
				RefTime = Time
				Tref = T
			if (Time - StartTime) >= Timeout:
				print "iTC: Warning: iTCWaitForStableT Timeout expired"
				Status = False
				break
			time.sleep(Interval)
		return T, Status

def stupid_waiting(t):
	if t > 1.:
		for i in range(int(t),0,-1):
			time.sleep(1)
			#print("Delay... {:d}   ".format(i),end = "\r")
		time.sleep( t - floor(t) )
	else:
		time.sleep(t)
		
def uniform_segment_table(Fstop,Npoints,Segments):
	Fstart = Segments[0]['start']
	Fstep = (Fstop-Fstart)/(float(Npoints)-1)
	ToFgrid = lambda x:  Fstart + round((x - Fstart)/Fstep)*Fstep
	SegTable = []
	for i,seg in enumerate(Segments):
		SegStart = ToFgrid(seg["start"])
		if i < (len(Segments)-1):
			SegStop = ToFgrid(Segments[i+1]["start"])-Fstep
		else:
			SegStop = Fstop
		SegPoints = int(round((SegStop-SegStart)/Fstep)+1 )
		SegTable+={'start':SegStart, 'stop':SegStop, 'points':SegPoints, 'power':seg['power'],'bandwidth':seg['bandwidth']}
	return SegTable	