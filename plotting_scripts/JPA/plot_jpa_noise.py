import tables
from matplotlib.pyplot import *
from numpy import *
import pickle
import scipy.constants as sc
import copy
from scipy.signal import *
import warnings
from anti_qsweepy.routines import gain_noise

db = lambda x: 10*log10(x)
dbm = lambda x: 10*log10(x/1e-3)
#Sources are at the input of HEMT amplifier

#Open HDF5 data file
noise_cal_file = "../noise_calibration/data.h5"
noise_cal_groupes = [1,2]
through_cal_file = "../through_calibration/data.h5"

window = 51
Noise = True
data_file = True
cal_file = True
through_file = True

try:
    if data_file:
        f = tables.open_file('data.h5', mode='r')
except:
    data_file = False
    warnings.warn("File data.h5 not found!")

if data_file:
    try:
        Spec_off = savgol_filter(array(f.root.Spec_off), window,3)
        Spec_on = savgol_filter(array(f.root.Spec_on), window,3)
        F_Spec = array(f.root.F_Spec)
    except:
        warnings.warn("Spectral data not found!")
        Noise = False

if Noise:
    try:
        f_cal = tables.open_file(noise_cal_file, mode='r')
        Tcal = []
        bw_cal=[]
        for group in noise_cal_groupes:
            Tcal += [f_cal.root.thumbnail[group-1]['temperature'],]
            bw_cal += [f_cal.root.thumbnail[group-1]['bandwidth'],]
        ind_h = argmax(Tcal)
        ind_l = argmin(Tcal)
        Th = Tcal[ind_h]
        Tl = Tcal[ind_l]
        bw = bw_cal[0]
        node = f_cal.get_node('/group_{:d}'.format(noise_cal_groupes[ind_h]))
        F_cal = np.array(node.F)
        P_cal_h = savgol_filter(node.P, window,3)
        node = f_cal.get_node('/group_{:d}'.format(noise_cal_groupes[ind_l]))
        P_cal_l = savgol_filter(node.P, window,3)
    except:
        warnings.warn("Calibration data not found!")
        cal_file = False

    subplot(2,3,1)
    title("Raw spectra, dBm")
    if data_file:
        plot(np.array(f.root.F_Spec), dbm(Spec_off), label = "Pump off")
        plot(np.array(f.root.F_Spec), dbm(Spec_on), label = "Pump on")
    if cal_file:
        plot(F_cal, dbm(P_cal_h), label = "Calibration high")
        plot(F_cal, dbm(P_cal_l), label = "Calibration low")
    legend()
    grid()

subplot(2,3,2)
title("S21, dB")
if data_file:
    F_S21 = array(f.root.F_S21)
    plot(F_S21, 2*db(f.root.S21_off), label = "Pump off" )
    plot(F_S21, 2*db(f.root.S21_on), label = "Pump on" )
    S21_on = abs(array(f.root.S21_on))
    S21_off = abs(array(f.root.S21_off))

if through_file and data_file:
    try:
        f_thr_cal = tables.open_file(through_cal_file, mode='r')
        S21_off = interp(F_S21,array(f_thr_cal.root.x), abs(array(f_thr_cal.root.y)) )
        plot(F_S21, 2*db(S21_off), label = "Through")
    except:
        through_file = False
        warnings.warn("Through calibration data not found!")

legend()
grid()

subplot(2,3,3)
title("Amplifier gain, dB")
if data_file:
    G_S21 = abs( S21_on/S21_off )
    G_S21 = S21_on/S21_off
    plot( F_S21, 2*db( G_S21 ))
    grid()

if Noise and cal_file:
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
    if data_file:
        plot(F_Spec, interp(F_Spec, F_cal,Tn)/Spec_off * Spec_on/( interp(F_Spec, F_S21,G_S21)**2 ), label="Amplifier noise" )
        plot(F_Spec, 4*pi*F_Spec*sc.hbar/(2*sc.k), '--', label = "Quantum limit")
        legend()
        grid()
show()