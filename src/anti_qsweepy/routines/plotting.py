from collections.abc import Iterable
from matplotlib.artist import Artist
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os
from abc import ABC, abstractmethod
import matplotlib.ticker as mpl_ticker
from pathlib import Path

def get_ticks(vmin, vmax):
    loc = mpl_ticker.MaxNLocator()
    raw = loc.tick_values(vmin,vmax)
    lo, hi = min(vmin, vmax), max(vmin, vmax)
    return raw[(raw >= lo) & (raw <= hi)]

class UpdatablePlot(ABC):
    """Updatable plot"""
    def __init__(self, filepath: str):
        # Update interval
        self.interval = 1000

        self.filename = filepath
        self._file_size = 0

        self.fig = self.create_figure()
        self.axs = self.create_axes()
        self.artists = self.create_plot()
        self.ani = animation.FuncAnimation(self.fig, self._update, interval=self.interval, blit=False, cache_frame_data=False)
        plt.show()

    def _check_file_size_changed(self) -> bool:
        res = False
        file_size = os.path.getsize(self.filename)
        #f = tables.open_file(self.filename, mode='r')
        #file_size = f.get_filesize()
        #f.close()
        if file_size != self._file_size:
            res = True
            self._file_size = file_size
        return res

    def _update(self, frame)->Iterable[Artist]:
        """Auto update the plot"""
        if self._check_file_size_changed():
            self.artists = self.update_plot()
        return self.artists

    def create_figure(self)->plt.Figure:
        """Create Matplotlib figure here"""
        cwd = Path(os.getcwd())
        return plt.figure(cwd.name)

    @abstractmethod
    def create_axes(self)->Iterable[plt.Axes]:
        """Create Matplotlib axes here"""
        pass

    @abstractmethod
    def create_plot(self)->Iterable[Artist]:
        """First time plot creation"""
        pass

    @abstractmethod
    def update_plot(self)->Iterable[Artist]:
        """Update the plot"""
        pass