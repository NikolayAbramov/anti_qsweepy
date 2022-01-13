import tables
from matplotlib.pyplot import *
from numpy import *
import scipy.constants as sc
from scipy.signal import *
db = lambda x: 10*log10(x)

#Open HDF5 data file
f = tables.open_file('data.h5', mode='r')

thumbnail = f.root.thumbnail
for record in thumbnail:
	node = f.get_node('/group_{:d}'.format(record['group_number']))
	plot( array(node.F)*1e-9, db(array(node.P)), label = '{:f}K'.format(record['temperature']))
xlabel("Frequency, GHz")
ylabel("Power, dBm")
legend()
show()