import tables
from numpy import *
from matplotlib.pyplot import *
from matplotlib.widgets import Button
import os
os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"

db = lambda x: 20*log10(x)

#Open HDF5 data file
f = tables.open_file('data.h5', mode='r')
n_records = len(f.root.thumbnail)

fig, axs = subplots(1,2)
fig.set_size_inches( (8, 4.8) )
fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.25)
group_n = 0

def plot_group(n):
	group = f.root['group_{:d}'.format(n)]
	F = array(group.frequency)
	#S21_off = array( group.pump_off )
	S21_on = array( group.pump_on )
	S21_off_snr = array( group.snr_pump_off )
	S21_off = mean(S21_off_snr, axis = 0)
	axs[0].clear()
	fig.suptitle("{:d}:Fc={:.5f}GHz Pp={:.2f}dBm I={:.4e}A, Gsnr = {:.2f} dB".format(n, 
														f.root.thumbnail[n]['Fs']*1e-9,
														f.root.thumbnail[n]['Pp'],
														f.root.thumbnail[n]['I'],
														f.root.thumbnail[n]['Gsnr']))
	axs[0].plot( F, db(abs(S21_off)), label = "Pump off" )
	axs[0].plot( F, db(abs(S21_on)) , label = "Pump on")
	axs[0].set_title("S21")
	axs[0].grid()
	axs[0].legend()
	axs[0].set_xlabel("Hz")
	axs[0].set_ylabel("dB")
	#Plot SNR
	
	snr_ref = abs(S21_off)/std(real(S21_off_snr), axis = 0)
	S21_on_snr = array( group.snr_pump_on )
	snr = abs(mean(S21_on_snr, axis = 0))/std(real(S21_on_snr), axis = 0)
	F_snr = array( group.snr_frequency )
	axs[1].clear()
	axs[1].plot(F_snr, 20*log10(snr/snr_ref), label = "SNR gain")
	axs[1].plot(F_snr, 20*log10(abs(S21_on/S21_off)), label = "Gain")
	axs[1].set_title("Gain")
	axs[1].set_xlabel("Hz")
	axs[1].set_ylabel("dB")
	axs[1].legend()
	fig.canvas.draw()
	
plot_group(group_n)	

def forward(event):
	global n_records
	global group_n
	#Open HDF5 data file
	if group_n < n_records-1:
		group_n += 1
	return plot_group(group_n)
	
def backward(event):
	global n_records
	global group_n
	#Open HDF5 data file
	if group_n > 0:
		group_n -= 1
	return plot_group(group_n)	

#m1,m2,m3 = update(0)

b_fwd = Button(axes([0.81, 0.05, 0.1, 0.075]), '>')
b_fwd.on_clicked(forward)

b_bwd = Button(axes([0.71, 0.05, 0.1, 0.075]), '<')
b_bwd.on_clicked(backward)
show()
