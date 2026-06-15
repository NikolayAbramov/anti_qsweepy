import matplotlib.pyplot as plt
import tables
from numpy import *
from matplotlib.pyplot import *
from scipy.signal import *
from anti_qsweepy.routines.plotting import UpdatablePlot, get_ticks

db = lambda x: 20*log10(x)

class Plot(UpdatablePlot):
    def plot(self):
        f = tables.open_file(self.filename, mode='r')
        data_2d = array(f.root.data)
        c_coord = array(f.root.column_coordinate)
        r_coord = array(f.root.row_coordinate)
        meshes = []
        data_2d_norm = data_2d / data_2d[0]
        # abs
        ax:plt.Axes = self.axs[0][0]
        ax.set_title('Amplitude, dB')
        meshes += [ax.pcolormesh( c_coord, r_coord, db(abs(data_2d)), shading='nearest' )]

        # Unwrapped phase
        uPh = unwrap(angle(data_2d))
        ax: plt.Axes = self.axs[0][1]
        ax.set_title('Unwrapped phase, rad')
        meshes += [ax.pcolormesh(c_coord, r_coord, uPh, shading='nearest')]

        # Normalized amplitude
        ax: plt.Axes = self.axs[0][2]
        ax.set_title('Normalized amplitude, dB')
        meshes += [ax.pcolormesh(c_coord, r_coord, db(abs(data_2d_norm)), shading='nearest')]

        # Normalized unwrapped phase
        ax: plt.Axes = self.axs[1][0]
        ax.set_title("normalized unwraped phase, rad")
        meshes += [ax.pcolormesh(c_coord, r_coord, unwrap(angle(data_2d_norm)), shading='nearest')]

        # Delay
        ax: plt.Axes = self.axs[1][1]
        ax.set_title("delay, ns")
        uPh_filt = savgol_filter(uPh, 51, 3)
        meshes += [ax.pcolormesh(c_coord[:-1], r_coord, -diff(uPh_filt) / ((c_coord[1] - c_coord[0]) * 2. * pi), shading='nearest')]
        #meshes[-1].set_clim(0, 0.5e-7)

        f.close()
        return meshes

    def create_axes(self):
        n_rows = 2
        n_cols = 3
        return self.fig.subplots(n_rows,n_cols)

    def create_plot(self):
        meshes = self.plot()
        for mesh in meshes:
            plt.colorbar(mesh)
        return meshes

    def update_plot(self):
        if self.artists is not None:
            for item in self.artists:
                item.remove()
        return self.plot()

if '__main__' == __name__:
    Plot("data.h5")