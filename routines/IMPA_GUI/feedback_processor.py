import multiprocessing as mp
import traceback as tb
import numpy.typing as nt
from typing import Any
import numpy as np
from dataclasses import fields
import queue

import data_structures as ds
import ui_callbacks as ui_cb


class FeedbackProcessor:
    def __init__(self, q_feedback: mp.Queue,
                 q_command: mp.Queue,
                 ui_objects: ds.UiObjects,
                 cb: ui_cb.UiCallbacks):
        self.ui_objects = ui_objects
        self.q_command = q_command
        self.q_feedback = q_feedback
        self.cb = cb

    @staticmethod
    def _connect_device(dev: ds.Device) -> None:
        dev.is_connected.update(True)
        dev.set_parameters_enable(True)
        dev.is_connected.enabled = True
        dev.initialized = True

    @staticmethod
    def _disconnect_device(dev: ds.Device) -> None:
        dev.is_connected.update(False)
        dev.set_parameters_enable(False)
        dev.is_connected.enabled = True
        dev.initialized = True

    def connect_pump_source(self, ch_id: int) -> None:
        dev = self.ui_objects.channel_tabs[ch_id].chan.pump_source
        self._connect_device(dev)

    def disconnect_pump_source(self, ch_id: int) -> None:
        dev = self.ui_objects.channel_tabs[ch_id].chan.pump_source
        self._disconnect_device(dev)

    def set_pump_output(self, val: bool, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.pump_source.output, val)

    def set_pump_power(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.pump_source.power, val)

    def set_pump_frequency(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.pump_source.frequency, val)

    def connect_bias_source(self, ch_id: int) -> None:
        dev = self.ui_objects.channel_tabs[ch_id].chan.bias_source
        self._connect_device(dev)

    def disconnect_bias_source(self, ch_id: int) -> None:
        dev = self.ui_objects.channel_tabs[ch_id].chan.bias_source
        self._disconnect_device(dev)

    def set_bias_current(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.bias_source.current, val)

    def set_bias_limit(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.bias_source.compliance_voltage, val)

    def set_bias_output(self, val: bool, ch_id: int):
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.bias_source.output, val)

    def connect_vna(self, ch_id:int):
        dev = self.ui_objects.channel_tabs[ch_id].chan.vna
        self._connect_device(dev)

    def disconnect_vna(self, ch_id):
        dev = self.ui_objects.channel_tabs[ch_id].chan.vna
        self._disconnect_device(dev)

    def _set_global_ui_lock(self, val: bool, except_ch_id: int) -> None:
        for ch_id in range(len(self.ui_objects.channel_tabs)):
            ch = self.ui_objects.channel_tabs[ch_id].chan
            ch.vna.set_parameters_enable(not val)
            ch.vna.is_connected.enabled = not val
            ch.vna.locked = val
            ch.bias_source.set_parameters_enable(not val)
            ch.pump_source.set_parameters_enable(not val)
            if ch_id != except_ch_id:
                ch.bias_sweep.is_running.enabled = not val
                ch.optimization.is_running.enabled = not val

    def set_vna_measurement_type(self, val: str, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.vna.measurement_type, val)

    def set_vna_power(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.vna.power, val)

    def set_vna_bandwidth(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.vna.bandwidth, val)

    def set_vna_points(self, val: int, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.vna.points, val)

    def set_vna_center(self, val: float, ch_id: int) -> None:
        vna = self.ui_objects.channel_tabs[ch_id].chan.vna
        vna.center.update(val)
        vna.center.confirmed = True
        if not vna.pump_center_bind.value:
            vna.center.enabled = True

    def set_vna_span(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.vna.span, val)

    def update_gain_plot(self, data: nt.ArrayLike, ch_id: int) -> None:
        data = np.array(data)
        tab = self.ui_objects.channel_tabs[ch_id]
        vna = tab.chan.vna
        if vna.normalize.value and vna.ref_data is not None:
            if np.min(data[0]) < np.min(vna.ref_data[0]) or \
                    np.max(data[0]) > np.max(vna.ref_data[0]):
                vna.normalize.update(False)
            else:
                ref = np.interp(data[0], vna.ref_data[0], vna.ref_data[1])
                data[1] = data[1]-ref
        else:
            vna.ref_data = data
        fig = tab.gain_fig
        trace_id = self.ui_objects.gain_plot_traces.vna_s21
        fig['data'][trace_id]['x'] = list(data[0]/1e9)
        fig['data'][trace_id]['y'] = list(data[1])
        fig['data'][trace_id]['name'] = 'VNA S21'
        #tab.gain_plot.run_method('Plotly.restyle', (str(tab.gain_plot.id), {}))
        tab.gain_plot.update()

    def start_bias_sweep(self, ch_id: int) -> None:
        ch = self.ui_objects.channel_tabs[ch_id].chan
        ch.bias_sweep.is_running.update(True)
        ch.bias_sweep.is_running.enabled = True
        ch.bias_sweep.set_parameters_enable(False)
        ch.optimization.set_parameters_enable(False)
        ch.optimization.is_running.enabled = False
        self._set_global_ui_lock(True, ch_id)

    def bias_sweep_progress(self, val: float, ch_id: int) -> None:
        ch = self.ui_objects.channel_tabs[ch_id].chan
        ch.bias_sweep.progress = np.round(val)

    def update_bias_sweep_plot(self, ch_id: int) -> None:
        self.cb.update_bias_sweep_plot_from_file(ch_id)

    def open_bias_sweep_file(self, path: str, ch_id: int) -> None:
        self.cb.open_bias_sweep_file(path, ch_id)

    def stop_bias_sweep(self, ch_id: int) -> None:
        ch = self.ui_objects.channel_tabs[ch_id].chan
        ch.bias_sweep.is_running.update(False)
        ch.bias_sweep.is_running.enabled = True
        ch.bias_sweep.set_parameters_enable(True)
        ch.optimization.set_parameters_enable(True)
        ch.optimization.is_running.enabled = True
        self._set_global_ui_lock(False, ch_id)
        # Restore devices settings
        for f in fields(ch.bias_source):
            attr = getattr(ch.bias_source, f.name)
            if ds.UIParameter in type(attr).mro() and attr.instrumental:
                self.cb.queue_param(ch_id, attr.get_value(), attr)
        for f in fields(ch.vna):
            attr = getattr(ch.vna, f.name)
            if ds.UIParameter in type(attr).mro() and attr.instrumental:
                self.cb.queue_param(ch_id, attr.get_value(), attr)

    def start_optimization(self, ch_id: int) -> None:
        ch = self.ui_objects.channel_tabs[ch_id].chan
        log = self.ui_objects.channel_tabs[ch_id].log
        ch.optimization.is_running.update(True)
        ch.optimization.is_running.enabled = True
        ch.optimization.set_parameters_enable(False)
        ch.bias_sweep.is_running.enabled = False
        ch.bias_sweep.set_parameters_enable(False)
        self._set_global_ui_lock(True, ch_id)
        log.push("Optimization started at {:s}".format(ch.name))

    def stop_optimization(self, ch_id: int) -> None:
        ch = self.ui_objects.channel_tabs[ch_id].chan
        log = self.ui_objects.channel_tabs[ch_id].log
        ch.optimization.is_running.update(False)
        ch.optimization.is_running.enabled = True
        ch.optimization.set_parameters_enable(True)
        ch.bias_sweep.is_running.enabled = True
        ch.bias_sweep.set_parameters_enable(True)
        # TODO add devices settings download from the instruments
        self._set_global_ui_lock(False, ch_id)
        log.push("Optimization stopped at {:s}".format(ch.name))

    @staticmethod
    def _update_param(p: ds.UIParameter, val: Any):
        p.update(val)
        p.enabled = True
        p.confirmed = True

    def check_queue(self) -> None:
        if self.ui_objects.app_state is ds.AppState.initial_devices_connection:
            if self.cb.check_devices_initialized():
                print("Setup")
                self.cb.setup_devices()
                self.ui_objects.app_state = ds.AppState.initialization_done

        if not self.q_feedback.empty():
            command = self.q_feedback.get()
            if command['op'] != "update_gain_plot":
                print("Main process got feedback: ", command['op'],command['args'])
            else:
                pass
                #print("Main process got feedback: ", command['op'])
            try:
                getattr(self, command['op'])(*command['args'])
            except Exception as err:
                tb.print_exc()

    def log_push(self, msg: str, ch_id):
        log = self.ui_objects.channel_tabs[ch_id].log
        log.push(msg)
