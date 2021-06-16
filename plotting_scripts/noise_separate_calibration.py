import tables
from matplotlib.pyplot import *
from numpy import *
import pickle
from qsweepy import gain_noise
import scipy.constants as sc
import copy
from scipy.signal import *

#Sources are at the input of HEMT amplifier

#Open HDF5 data file
f = tables.open_file('data.h5', mode='r')

#Miliwatts!
window = 51
Spec_off = savgol_filter(array(f.root.Spec_off)/1000., window,3)
Spec_on = savgol_filter(array(f.root.Spec_on)/1000., window,3)
F_S21 = array(f.root.F_S21)
F_Spec = array(f.root.F_Spec)


high_cal_file = "../noise_calibration_data/3.96K.csv"
Th = 3.96
low_cal_file = "../noise_calibration_data/37mK.csv"
Tl = 0.037
bw = 250e3

data = loadtxt(high_cal_file, delimiter = ",").T
F_cal = array(data[0])*1e6
P_cal_h = savgol_filter(10**(array(data[1])/10.)/1000., window,3)

data = loadtxt(low_cal_file, delimiter = ",").T
P_cal_l = savgol_filter(10**(array(data[1])/10.)/1000., window,3)

db = lambda x: 10*log10(x)

subplot(2,3,1)
title("Raw spectra, dBm")
plot(f.root.F_Spec, Spec_off, label="Pump off")
plot(f.root.F_Spec, Spec_on, label = "Pump on")
plot(F_cal, P_cal_h, label = "Calibration high")
plot(F_cal, P_cal_l, label = "Calibration low")
legend()
grid()
print (F_cal)

subplot(2,3,2)
title("S21, dB")
plot(f.root.F_S21, 2*db(f.root.S21_off), label="Pump off" )
plot(f.root.F_S21, 2*db(f.root.S21_on), label = "Pump on" )
legend()
grid()

subplot(2,3,3)
title("Amplifier gain, dB")
G_S21 = abs( array(f.root.S21_on)/array(f.root.S21_off) )
plot( f.root.F_S21, 2*db( G_S21 ))
grid()


G, Tn = gain_noise.gain_noise(F_cal, [P_cal_l, P_cal_h],
	[[Tl, 1]], [[Th, 1]] )


subplot(2,3,4)
title("Measurement system noise, K")
plot(F_cal, Tn)
#ylim([0,1])
grid()

subplot(2,3,5)
title("Measurement system gain, dB")
plot(F_cal, db(G/bw) )
grid()

subplot(2,3,6)
title("Amplifier noise, K")
plot(F_Spec, interp(F_Spec, F_cal,Tn)/Spec_off * Spec_on/( interp(F_Spec, F_S21,G_S21)**2 ), label="Amplifier noise" )
plot(F_Spec, 2*pi*F_Spec*sc.hbar/(2*sc.k), '--', label = "Quantum limit")
legend()
grid()

show()