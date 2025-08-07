from numpy import *
from scipy.signal import *
import scipy.optimize as so

def group_delay(F, S):
	uPh = unwrap(angle(S))
	slope_est = (uPh[-1] - uPh[0])/(F[-1] - F[0])
	c0_est = uPh[0]-F[0]*slope_est
	popt,pcov = so.curve_fit(lambda x,c0,slope: c0 + slope*x, F, uPh, p0 = (c0_est,slope_est))
	return -popt[1]/(2.*pi)
	
def delay(F,S, window = None):
	uPh = unwrap(angle(S))
	if window is not None:
		uPh = savgol_filter(uPh, window,3)
	delay = -diff(uPh)/((F[1]-F[0])*2.*pi)
	delay = concatenate( (delay[0:1], delay) )
	return delay