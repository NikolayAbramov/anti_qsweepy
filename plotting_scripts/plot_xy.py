import tables
from numpy import *
from matplotlib.pyplot import *

#Open HDF5 data file
f = tables.open_file('data.h5', mode='r')

db = lambda x: 20*log10(x)
print(f.root.x.title)
x = array(f.root.x)
y = array(f.root.y)

plot( x, y )
xlabel(f.root.x.title)
ylabel(f.root.y.title)
show()

f.close()