from anti_qsweepy.drivers import *
from anti_qsweepy.routines import data_mgmt
from anti_qsweepy.routines.helper_functions import *
import numpy as np
from dataclasses import dataclass
from concurrent.futures import Future
import multiprocessing as mp
import time

min_plot_update_interval = 1

@dataclass
class BiasSweepParameters:
    ch_id: int
    bias_start: float
    bias_stop: float
    bias_step: float
    vna_start: float
    vna_stop: float
    vna_points: int
    vna_power: float
    vna_bandwidth: float
    save_path: str


class BiasSweep:
    def __init__(self, bias_source, vna, q: mp.Queue, params: BiasSweepParameters):
        self.q = q
        self.vna = vna
        self.bias_source = bias_source
        self.params: BiasSweepParameters = params
        self.future: Future|None = None
        self._abort: bool = False
        self.params.save_path = data_mgmt.default_save_path(self.params.save_path, name="SvsBias")

    def abort(self):
        self._abort = True
        self.vna.abort()

    def sweep(self):
        self._abort = False
        bias_vals = np.arange(self.params.bias_start,
                              self.params.bias_stop,
                              self.params.bias_step)
        progress_percent_step = 100/len(bias_vals)
        plotting_script = "plot_2d_S"
        row_descr = "Current, A"
        self.vna.num_of_points(self.params.vna_points)
        self.vna.freq_start_stop((self.params.vna_start,
                                  self.params.vna_stop))
        self.vna.bandwidth(self.params.vna_bandwidth)
        self.vna.power(self.params.vna_power)
        self.vna.sweep_type("LIN")
        self.bias_source.channel(self.params.ch_id)
        Fna = self.vna.freq_points()
        f, d_array, r_array = data_mgmt.extendable_2d(self.params.save_path, Fna, row_descr=row_descr)
        self.q.put({'op': 'open_bias_sweep_file', 'args': (self.params.save_path+r'\data.h5', self.params.ch_id)})
        data_mgmt.spawn_plotting_script(self.params.save_path, plotting_script)
        self.vna.output(True)
        self.bias_source.output(True)
        self.vna.soft_trig_arm()
        progress = 0
        t_start = time.time()
        for bias_val in bias_vals:
            self.bias_source.setpoint(bias_val)
            S = self.vna.read_data()
            if self._abort:
                self._abort = False
                break
            d_array.append(S.reshape(1, len(S)))
            r_array.append(array([bias_val]))
            f.flush()
            progress += progress_percent_step
            self.q.put({'op': 'bias_sweep_progress', 'args': (progress, self.params.ch_id)})
            if time.time()-t_start > min_plot_update_interval:
                self.q.put({'op': 'update_bias_sweep_plot', 'args': (self.params.ch_id,)})
                t_start = time.time()
        self.bias_source.output(False)
        self.vna.soft_trig_abort()
        f.close()
        self.q.put({'op': 'stop_bias_sweep', 'args': (self.params.ch_id,)})