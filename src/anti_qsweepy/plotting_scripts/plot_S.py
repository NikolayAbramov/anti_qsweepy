import tables
from numpy import *
from matplotlib.pyplot import *
from scipy.signal import *

#Open HDF5 data file
f = tables.open_file('data.h5', mode='r')

db = lambda x: 20*log10(x)

x = array(f.root.x)
y = array(f.root.y)

subplot(1,3,1)
title("Amplitude, dB")
plot( x, db(abs(y)) )

subplot(1,3,2)
title("Unwraped phase, rad")
uPh = unwrap(angle(y))
plot( x, uPh )

subplot(1,3,3)
title("delay, ns")
uPh_filt = savgol_filter(uPh, 11,3)
plot( x[1::], -diff(uPh_filt)/((x[1]-x[0])*2.*pi) )
#clim((0.5e-7,0.6e-7))

show()

f.close()