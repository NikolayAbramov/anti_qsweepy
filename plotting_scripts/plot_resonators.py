import tables
from numpy import *
from matplotlib.pyplot import *
from scipy.signal import *

diff_step = 2
#Open HDF5 data file
f = tables.open_file('data.h5', mode='r')

db = lambda x: 20*log10(x)
data_2d = array(f.root.data)
c_coord = array(f.root.column_coordinate)
r_coord = array(f.root.row_coordinate)
segment_table = f.root.segment_table
print(segment_table[0]['points'])
print(len(segment_table))

data_2d_norm = data_2d/data_2d[0]
data_abs = abs(data_2d)

subplot(2,3,1)
title("amplitude, dB")
pcolormesh(  r_coord, c_coord, db(data_abs).T, shading='nearest' )
colorbar()

subplot(2,3,2)
title("amplitude diff")
data_for_diff = data_abs.T
diff_data = hstack( (data_for_diff[::, diff_step::], data_for_diff[::, 0:diff_step]) ) - data_for_diff
diff_data = diff_data.T
pcolormesh(  r_coord, c_coord, diff_data.T , shading='nearest')
set_cmap( get_cmap(name = 'bwr') )
clim_diff = (-2e-5,2e-5)
clim(clim_diff)
colorbar()

subplot(2,3,3)
title("amplitude norm. by start, dB")
pcolormesh(  r_coord, c_coord, db(abs(data_2d_norm)).T, shading='nearest' )
set_cmap( get_cmap(name = 'viridis') )
colorbar()

show()
clf()
title("amplitude, dB")
pcolormesh( r_coord, c_coord, db(data_abs).T, shading='nearest' )
colorbar()

limits = 	[[4.3e9,4.5e9],
			[5.8e9,6.2e9]]
for i in range(len(segment_table)):
	#ylim((segment_table[i]['start'], segment_table[i]['stop']))
	ylim(limits[i])
	savefig("{:d}_amp.png".format(i),dpi=300)

clf()
title("amplitude diff")
data_for_diff = data_abs.T
diff_data = hstack( (data_for_diff[::, diff_step::], data_for_diff[::, 0:diff_step]) ) - data_for_diff
diff_data = diff_data.T
pcolormesh(  r_coord, c_coord, diff_data.T, shading='nearest' )
set_cmap( get_cmap(name = 'bwr') )
clim(clim_diff)
colorbar()
savefig("diff.png",dpi=300)
f.close()
