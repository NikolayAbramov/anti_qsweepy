# Plot all data from HDF5 file containing multiple groups with xy data in its root

import tables
from numpy import *
from matplotlib.pyplot import *

#Open HDF5 data file
f = tables.open_file('data.h5', mode='r')

print(f)
n_groups = 0
for group in f.walk_groups():
    n_groups +=1
    
if n_groups > 0:    
    n_groups = n_groups-1
else:
    raise Exception('No usable groups in the file!')

db = lambda x: 20*log10(x)
group_idx = 1
for group in f.walk_groups():
    try:
        x = array( group.x )
        y = array( group.y )
        subplot(n_groups,1, group_idx)
        plot(x,y, label = str(group))
        xlabel(group.x.title)
        ylabel(group.y.title)
        legend()
        group_idx += 1
    except tables.exceptions.NoSuchNodeError:
        print("Group {0} missing required nodes".format(group))

show()

f.close()