import tables
from numpy import *
from matplotlib.pyplot import *
from matplotlib.widgets import Button

db = lambda x: 20*log10(x)

#Open HDF5 data file
f = tables.open_file('data.h5', mode='r')
n_records = len(f.root.thumbnail)

fig, ax1 = subplots()
fig.subplots_adjust(left=0.07, right=0.95, top=0.95, bottom=0.2)
group_n = 0

def plot_group(n):
	group = f.root['group_{:d}'.format(n)]
	F = array(group.frequency)
	S21_off = array( group.pump_off )
	S21_on = array( group.pump_on )
	ax1.clear()
	ax1.set_title("{:d}:Fc={:.5f}GHz Pp={:.2f}dBm I={:.4e}A, Gsnr = {:.2f} dB".format(n, 
														f.root.thumbnail[n]['Fs']*1e-9,
														f.root.thumbnail[n]['Pp'],
														f.root.thumbnail[n]['I'],
														f.root.thumbnail[n]['Gsnr']))
	p1 = ax1.plot( F, db(abs(S21_off)) )
	p2 = ax1.plot( F, db(abs(S21_on)) )
	fig.canvas.draw()
	return p1,p2
	
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
