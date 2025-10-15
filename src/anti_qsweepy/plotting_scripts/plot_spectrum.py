import tables
from numpy import *
from matplotlib.pyplot import *

"""Script for plotting specrum analizer data"""

f = tables.open_file('data.h5', mode='r')

print(f.root.x.title)
x = array(f.root.x)
y = array(f.root.y)

y = log10(y/1e-3)*10

fig,axs = subplots(1,1)
fig.canvas.manager.set_window_title('SA data')
fig.suptitle("rbw={0}Hz, vbw={1}Hz".format(f.root.metadata[0]['rbw'], f.root.metadata[0]['vbw']))
axs.plot( x, y )
axs.set_xlabel(f.root.x.title)
axs.set_ylabel("Power, dBm")
show()

f.close()