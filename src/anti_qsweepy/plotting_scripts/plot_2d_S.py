import tables
from numpy import *
from matplotlib.pyplot import *
from scipy.signal import *
import os
os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"

#Open HDF5 data file
f = tables.open_file('data.h5', mode='r')

db = lambda x: 20*log10(x)
data_2d = array(f.root.data)
c_coord = array(f.root.column_coordinate)
r_cord = array(f.root.row_coordinate)

data_2d_norm = data_2d/data_2d[0]

subplot(2,3,1)
title("amplitude, dB")
pcolormesh( c_coord, r_cord, db(abs(data_2d)), shading='nearest' )
colorbar()

subplot(2,3,2)
title("unwraped phase, rad")
uPh = unwrap(angle(data_2d))
pcolormesh( c_coord, r_cord, uPh, shading='nearest' )
colorbar()

subplot(2,3,3)
title("normalized amplitude, dB")
pcolormesh( c_coord, r_cord, db(abs(data_2d_norm)), shading='nearest' )
colorbar()

subplot(2,3,4)
title("normalized unwraped phase, rad")
pcolormesh( c_coord, r_cord, unwrap(angle(data_2d_norm)), shading='nearest' )
colorbar()

subplot(2,3,5)
title("delay, ns")
uPh_filt = savgol_filter(uPh, 51,3)
pcolormesh( c_coord[:-1], r_cord, -diff(uPh_filt)/((c_coord[1]-c_coord[0])*2.*pi), shading='nearest' )
#clim((0.5e-7,0.6e-7))
colorbar()

show()

f.close()
