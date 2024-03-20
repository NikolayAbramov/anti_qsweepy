import queue
import traceback as tb
from dataclasses import fields
from typing import Any

import data_structures as ds
import multiprocessing as mp
from file_picker.local_file_picker import local_file_picker
from hdf5_gain import HDF5GainFile
from hdf5_bias_sweep import HDF5BiasSweepFile


class UiCallbacks:
    def __init__(self, ui_objects: ds.UiObjects, q_command: mp.Queue):
        self.q_command = q_command
        self.ui_objects = ui_objects

    def _connect_device(self, device: ds.Device, ch_id: int) -> None:
        driver_name = device.driver_name
        class_name = device.class_name
        address = device.address
        self.q_command.put({'op': device.connect_method,
                            'args': (driver_name, class_name, address, ch_id)})

    def _disconnect_device(self, device: ds.Device, ch_id: int) -> None:
        self.q_command.put({'op': device.disconnect_method,
                            'args': (ch_id,)})

    def init_devices(self):
        num_ch = len(self.ui_objects.channel_tabs)
        for ch_id in range(num_ch):
            chan = self.ui_objects.channel_tabs[ch_id].chan
            for f in fields(chan):
                attr = getattr(chan, f.name)
                if ds.Device in type(attr).mro():
                    if attr.is_connected.value:
                        self._connect_device(attr, ch_id)

    def change_float_param(self, ch_id: int, p: ds.FloatUIParam) -> None:
        self._queue_param(ch_id, p.get_value(), p)

    def toggle_bool_param(self, ch_id: int, p: ds.BoolUIParameter) -> None:
        self._queue_param(ch_id, not p.value, p)

    def inc_param(self, ch_id: int, p: ds.FloatUIParam) -> None:
        self._queue_param(ch_id, p.inc(), p)

    def dec_param(self, ch_id: int, p: ds.FloatUIParam) -> None:
        self._queue_param(ch_id, p.dec(), p)

    def _queue_param(self, ch_id, val: Any,  p: ds.UIParameter) -> bool:
        try:
            self.q_command.put({'op': p.method, 'args': (val, ch_id)})
        except queue.Full:
            p.update_str()
            return False
        else:
            p.enabled = False
            return True

    def _queue_command(self, op: str, args: tuple) -> bool:
        try:
            self.q_command.put({'op': op, 'args': args})
        except queue.Full:
            return False
        else:
            return True

    async def pick_gain_file(self, ch_id: int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        result = await local_file_picker('~', multiple=False)
        if result is not None:
            result = result[0]
            try:
                tab.gain_file = HDF5GainFile(result, mode='r')
            except Exception:
                tab.log.push("Unable to open file:" + result)
                tb.print_exc()
            else:
                tab.log.push("Opened gain file:" + result)
                tab.gain_file_toolbar_enabled = True
                if not self.update_gain_plot_from_file(ch_id):
                    self.close_gain_file(ch_id)

    def update_gain_plot_from_file(self, ch_id: int) -> bool:
        tab = self.ui_objects.channel_tabs[ch_id]
        data = tab.gain_file.get_data()
        if data['status']:
            gain_trace_id = self.ui_objects.gain_plot_traces.file_gain
            snr_gain_trace_id = self.ui_objects.gain_plot_traces.file_snr_gain
            tab.gain_fig['data'][gain_trace_id]['x'] = data['frequency']
            tab.gain_fig['data'][gain_trace_id]['y'] = data['gain']
            tab.gain_fig['data'][gain_trace_id]['name'] = 'Gain'
            tab.gain_fig['data'][snr_gain_trace_id]['x'] = data['frequency']
            tab.gain_fig['data'][snr_gain_trace_id]['y'] = data['snr_gain']
            tab.gain_fig['data'][snr_gain_trace_id]['name'] = 'SNR gain'
            tab.gain_fig['layout']['annotations'][0]['text'] = data['info']
            tab.gain_plot.update()
            tab.bias_sweep_fig['data'][1]['x'] = [data['Ib'], ]
            tab.bias_sweep_fig['data'][1]['y'] = [data['Fs'], ]
            # tab.bias_sweep_plot.update()
            return True
        else:
            tab.log.push(data['message'])
            return False

    def browse_gain_file_left(self, ch_id: int):
        tab = self.ui_objects.channel_tabs[ch_id]
        if tab.gain_file.backward():
            self.update_gain_plot_from_file(ch_id)

    def browse_gain_file_right(self, ch_id: int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        if tab.gain_file.forward():
            self.update_gain_plot_from_file(ch_id)

    def close_gain_file(self, ch_id: int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        fig = tab.gain_fig
        fig['data'][2] = dict(ds.default_gain_fig_data)
        fig['data'][3] = dict(ds.default_gain_fig_data)
        fig['layout']['annotations'][0]['text'] = ''
        tab.gain_plot.update()
        tab.log.push("Gain file closed:" + tab.gain_file.filename)
        tab.gain_file.close()
        del tab.gain_file
        tab.gain_file_toolbar_enabled = False

    async def pick_bias_sweep_file(self, ch_id: int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        result = await local_file_picker('~', multiple=False)
        if result is not None:
            result = result[0]
            self.open_bias_sweep_file(result, ch_id)

    def open_bias_sweep_file(self, path: str, ch_id: int, log: bool = True) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        old_filename = ''
        if tab.bias_sweep_file is not None:
            old_filename = tab.bias_sweep_file.filename
            tab.bias_sweep_file.close()
        try:
            tab.bias_sweep_file = HDF5BiasSweepFile(path, mode='r')
        except Exception:
            tab.bias_sweep_file = HDF5BiasSweepFile(old_filename, mode='r')
            tab.log.push("Unable to open file:" + path)
            tb.print_exc()
        else:
            if log:
                tab.log.push("Opened bias sweep file:" + path)
            tab.bias_sweep_file_toolbar_enabled = True
            if not self.update_bias_sweep_plot(ch_id):
                self.close_bias_sweep_file(ch_id)

    def update_bias_sweep_plot_from_file(self, ch_id: int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        filename = tab.bias_sweep_file.filename
        self.open_bias_sweep_file(filename, ch_id, log=False)

    def update_bias_sweep_plot(self, ch_id: int) -> bool:
        tab = self.ui_objects.channel_tabs[ch_id]
        data = tab.bias_sweep_file.get_data()
        if data['status']:
            tab.bias_sweep_fig['data'][0]['x'] = data['current']
            tab.bias_sweep_fig['data'][0]['y'] = data['frequency']
            tab.bias_sweep_fig['data'][0]['z'] = data['delay'].tolist()
            tab.bias_sweep_plot.update()
            return True
        else:
            tab.log.push(data['message'])
            return False

    def close_bias_sweep_file(self, ch_id: int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        tab.log.push("Bias sweep file closed:" + tab.bias_sweep_file.filename)
        tab.bias_sweep_file.close()
        del tab.bias_sweep_file
        tab.bias_sweep_file_toolbar_enabled = False
        tab.bias_sweep_fig['data'][0]['x'] = []
        tab.bias_sweep_fig['data'][0]['y'] = []
        tab.bias_sweep_fig['data'][0]['z'] = []
        tab.bias_sweep_plot.update()

    def toggle_vna_connection(self, ch_id):
        tab = self.ui_objects.channel_tabs[ch_id]
        try:
            if not tab.chan.vna.is_connected.value:
                self._connect_device(tab.chan.vna, ch_id)
            else:
                self._disconnect_device(tab.chan.vna, ch_id)
        except queue.Full:
            pass
        else:
            tab.chan.vna.is_connected.enabled = False

    def bind_pump_freq_to_vna_center(self, ch_id):
        ch_tab = self.ui_objects.channel_tabs[ch_id]
        p = ch_tab.chan.vna.center
        if ch_tab.chan.vna.pump_center_bind.value:
            p.enabled = False
            val = ch_tab.chan.pump_source.frequency.get_value()/2
            self._queue_param(ch_id, val, p)
        else:
            p.enabled = True

    def request_vna_data(self):
        ch_id = 0
        tab = self.ui_objects.channel_tabs[ch_id]
        status = tab.chan.vna.is_connected.value
        if status and self.q_command.empty():
            self.q_command.put({'op': 'get_vna_data', 'args': (ch_id,)})

    def set_pump_freq(self, ch_id: int, p: ds.UIParameter) -> None:
        ch_tab = self.ui_objects.channel_tabs[ch_id]
        if ch_tab.chan.vna.pump_center_bind.value:
            val = ch_tab.chan.pump_source.frequency.get_value() / 2
            self._queue_param(ch_id, val, ch_tab.chan.vna.center)
        self.change_float_param(ch_id, ch_tab.chan.pump_source.frequency)

    def inc_pump_freq(self, ch_id: int, p: ds.FloatUIParam) -> None:
        ch_tab = self.ui_objects.channel_tabs[ch_id]
        pump_freq = ch_tab.chan.pump_source.frequency.inc()
        self._queue_pump_freq(ch_id, pump_freq)

    def dec_pump_freq(self, ch_id: int, p: ds.FloatUIParam) -> None:
        ch_tab = self.ui_objects.channel_tabs[ch_id]
        pump_freq = ch_tab.chan.pump_source.frequency.dec()
        self._queue_pump_freq(ch_id, pump_freq)

    def _queue_pump_freq(self, ch_id: int, pump_freq: float) -> None:
        ch_tab = self.ui_objects.channel_tabs[ch_id]
        if ch_tab.chan.vna.pump_center_bind.value:
            vna_center = pump_freq/2
            self._queue_param(ch_id, vna_center, ch_tab.chan.vna.center)
        self._queue_param(ch_id, pump_freq, ch_tab.chan.pump_source.frequency)

    def start_stop_bias_sweep(self, ch_id: int) -> None:
        ch = self.ui_objects.channel_tabs[ch_id].chan
        if not ch.bias_sweep.is_running.value:
            data = {'ch_id': ch_id}
            for f in fields(ch.bias_sweep):
                attr = getattr(ch.bias_sweep, f.name)
                if ds.UIParameter in type(attr).mro() and attr.instrumental:
                    data.update({f.name: attr.value})
            data.update({'save_path': r'D:\IMPA'})
            if ch.pump_source.is_connected.value:
                self._queue_command('set_pump_output', (False, ch_id))
            if ch.vna.is_connected.value and ch.pump_source.is_connected.value:
                if self._queue_command('start_bias_sweep', (data,)):
                    ch.bias_sweep.progress = 0
                    ch.bias_sweep.is_running.enabled = False
        else:
            if self._queue_command('abort_bias_sweep', (ch_id,)):
                ch.bias_sweep.is_running.enabled = False
