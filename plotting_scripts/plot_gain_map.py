import tables
from numpy import *
from matplotlib.pyplot import *

#Open HDF5 data file
f = tables.open_file('data.h5', mode='r')

db = lambda x: 20*log10(x)

group = "/_1"
ref = array(f.get_node(group+'/reference')).T
data_2d = array(f.get_node(group+'/data'))
c_coord = array(f.get_node(group+'/column_coordinate'))
r_cord = array(f.get_node(group+'/row_coordinate'))
'''
data_2d = array(f._1.data)
c_coord = array(f._1.column_coordinate)
r_cord = array(f.root.row_coordinate)
'''
figure("map")
pcolormesh( c_coord, r_cord, db(abs(data_2d/ref)) )
colorbar()

figure("slice")
n = 42
print(r_cord[n])
plot( c_coord, db(abs(data_2d[n]/ref)) )
show()
f.close()