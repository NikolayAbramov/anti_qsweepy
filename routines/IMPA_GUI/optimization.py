from anti_qsweepy.routines import data_mgmt
from anti_qsweepy.routines.helper_functions import *
import anti_qsweepy.routines.jpa_tuning as jt
from phy_devices import PhyDevice
from std_output_catcher import StdOutputCatcher

import numpy as np
from dataclasses import dataclass
from concurrent.futures import Future
import multiprocessing as mp
import time
import tables

min_plot_update_interval = 1


@dataclass
class OptimizationParameters:
    ch_id: int
    target_gain: float  # dB
    target_bandwidth: float
    target_frequency: list[float]
    frequency_span: float
    bias_bond_1: float
    bias_bond_2: float
    pump_power_bond_1: float
    pump_power_bond_2: float
    w_cent: float
    vna_points: int
    vna_bandwidth: float
    vna_power: float
    popsize: int
    minpopsize: int
    threshold: float
    maxiter: int
    std_tol: float
    save_path: str


class Optimization:
    def __init__(self, bias_source: PhyDevice,
                 pump_source: PhyDevice,
                 vna: PhyDevice,
                 q: mp.Queue,
                 params: OptimizationParameters):
        self.q = q
        self.vna = vna
        self.bias_source = bias_source
        self.pump_source = pump_source
        self.params: OptimizationParameters = params
        self.future: Future | None = None
        self.params.save_path = data_mgmt.default_save_path(self.params.save_path, name="jpa_tuning")
        self.tuner: jt.IMPATuner| None = None
        self._abort = False

    def abort(self):
        self._abort = True
        self.tuner.abort()

    def start(self):
        # Tuner settings
        bias_source = self.bias_source.dev_inst
        bias_source.channel(self.pump_source.chan)
        pump_source = self.pump_source.dev_inst
        pump_source.channel(self.pump_source.chan)
        vna = self.vna.dev_inst
        vna.channel(self.vna.chan)
        self.tuner = jt.IMPATuner(vna=vna, pump=pump_source, bias=bias_source)
        self.tuner.bias_range = (self.params.bias_bond_1, self.params.bias_bond_2)
        self.tuner.pump_range = (self.params.pump_power_bond_1, self.params.pump_power_bond_2)
        self.tuner.target_gain = self.params.target_gain
        self.tuner.target_bw = self.params.target_bandwidth
        self.tuner.target_freq_span = self.params.frequency_span
        self.tuner.Ps = self.params.vna_power
        self.tuner.bw = self.params.vna_bandwidth
        self.tuner.points = self.params.vna_points
        self.tuner.w_cent = self.params.w_cent  # Weight of central point. If <1 helps to get a more flat gain.

        data_mgmt.spawn_plotting_script(self.params.save_path, "JPA\\plot_jpa_tuning_results")
        file = open(self.params.save_path + '/tuning_table.txt', 'w+')
        file.write(jt.OperationPoint().file_str_header())

        hdf5_title = 'JPA tuning table'

        class Thumbnail(tables.IsDescription):
            group_name = tables.StringCol(16)  # 16-character String
            group_number = tables.Int32Col()
            Fp = tables.Float64Col()
            Fs = tables.Float64Col()
            G = tables.Float64Col()
            Pp = tables.Float64Col()
            I = tables.Float64Col()
            Gsnr = tables.Float64Col()

        f = tables.open_file(self.params.save_path + '\\data.h5', mode='w', title=hdf5_title)
        thumbnail = f.create_table(f.root, 'thumbnail', Thumbnail, "thumbnail").row
        group_n = 0
        for f_cent in self.params.target_frequency:
            self.tuner.target_freq = f_cent
            with StdOutputCatcher(self.q, self.params.ch_id):
                op, status = self.tuner.find_gain(popsize=self.params.popsize,
                                                 minpopsize=self.params.minpopsize,
                                                 tol=0.01,
                                                 std_tol=self.params.std_tol,
                                                 maxiter=self.params.maxiter,
                                                 threshold=self.params.threshold,
                                                 disp=True)
            if self._abort:
                self._abort = False
                break
            file.write('\n' + op.file_str())
            file.flush()

            thumbnail['group_name'] = 'group_{:d}'.format(group_n)
            thumbnail['group_number'] = group_n
            thumbnail['Fs'] = op.Fs
            thumbnail['Fp'] = op.Fp
            thumbnail['G'] = op.G
            thumbnail['Pp'] = op.Pp
            thumbnail['I'] = op.I
            thumbnail['Gsnr'] = op.Gsnr
            thumbnail.append()
            f.flush()

            S21on, S21off, Fpoints = self.tuner.vna_snapshot(op)
            group = f.create_group(f.root, 'group_{:d}'.format(group_n), "S21")
            f.create_array(group, 'pump_on', S21on, "S21")
            f.create_array(group, 'pump_off', S21off, "S21")
            f.create_array(group, 'frequency', Fpoints, "Frequency, Hz")
            f.flush()

            S21on, S21off, Fpoints = self.tuner.snr_snapshot(op, Nmeas=100)
            f.create_array(group, 'snr_pump_on', S21on, "S21")
            f.create_array(group, 'snr_pump_off', S21off, "S21")
            f.create_array(group, 'snr_frequency', Fpoints, "Frequency, Hz")
            f.flush()

            group_n += 1

        f.close()
        file.close()
        self.q.put({'op': 'stop_optimization', 'args': (self.params.ch_id,)})
