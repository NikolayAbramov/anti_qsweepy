from matplotlib.pyplot import *
from numpy import *
import pickle
from qsweepy import gain_noise
import scipy.constants as sc

#Sources are at the input of HEMT amplifier

data = pickle.load(open('raw_data.pkl', 'rb'))

#Miliwatts!
data['S']['cold']['P'] = data['S']['cold']['P']/1000.
data['S']['hot']['P'] = data['S']['hot']['P']/1000.
data['S']['signal']['P'] = data['S']['signal']['P']/1000.

G, Tn = gain_noise.gain_noise(data['F_S'], [data['S']['cold']['P'], data['S']['hot']['P']],
	[[data['S']['cold']['T'], 1]], 
	[[data['S']['hot']['T'], 1]] )
	
print(data['S']['cold']['T'], 	data['S']['hot']['T'])

#[data['S']['cold']['T'], 1-a]

subplot(2,3,1)
title("Raw spectra, dBm")
plot(data['F_S'], 10*log10(data['S']['cold']['P']), label="Cold, {:.4f}K".format(data['S']['cold']['T']))
plot(data['F_S'], 10*log10(data['S']['hot']['P']), label = "Hot, {:.4f}K".format(data['S']['hot']['T']))
plot(data['F_S'], 10*log10(data['S']['signal']['P']), label = "Signal")
legend()
grid()

subplot(2,3,2)
title("S21, dB")
plot(data['F_S21'], 20*log10( abs(data['S21_off'])), label="Pump off" )
plot(data['F_S21'], 20*log10( abs(data['S21_on'])), label = "Pump on" )
legend()
grid()

subplot(2,3,3)
title("Amplifier gain, dB")
G_S21 = abs(data['S21_on']/data['S21_off'])
plot( data['F_S21'], 20*log10( G_S21 ))
grid()

subplot(2,3,4)
title("Measurement system noise, K")
plot(data['F_S'], Tn)
#ylim([0,1])
grid()

subplot(2,3,5)
title("Measurement system gain, dB")
plot(data['F_S'], 10*log10(G/data['BW']) )
grid()

subplot(2,3,6)
title("Amplifier noise, K")
plot(data['F_S'], Tn/data['S']['cold']['P']*data['S']['signal']['P']/( interp(data['F_S'],data['F_S21'],G_S21)**2 ), label="Amplifier noise" )
plot(data['F_S'], 2*pi*data['F_S']*sc.hbar/(2*sc.k), '--', label = "Quantum limit")
legend()
grid()

show()