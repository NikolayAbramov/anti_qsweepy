import queue
import traceback as tb
from dataclasses import fields

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
                print(type(attr).mro())
                if ds.Device in type(attr).mro():
                    if attr.is_connected.value:
                        self._connect_device(attr, ch_id)

    def change_float_param(self, ch_id: int, p: ds.FloatUIParam) -> None:
        val = p.get_value()
        if not self._queue_param(ch_id, val, p.method):
            p.update_str()
        else:
            p.enabled = False

    def toggle_bool_param(self, ch_id: int, p: ds.BoolUIParameter) -> None:
        if self._queue_param(ch_id, not p.value, p.method):
            p.enabled = False

    def inc_param(self, ch_id: int, p: ds.FloatUIParam) -> None:
        self._queue_param(ch_id, p.inc(), p.method)

    def dec_param(self, ch_id: int, p: ds.FloatUIParam) -> None:
        self._queue_param(ch_id, p.dec(), p.method)

    def _queue_param(self, ch_id, val: float,  method: str) -> bool:
        try:
            self.q_command.put({'op': method, 'args': (val, ch_id)})
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
            try:
                tab.bias_sweep_file = HDF5BiasSweepFile(result, mode='r')
            except Exception:
                tab.log.push("Unable to open file:" + result)
                tb.print_exc()
            else:
                tab.log.push("Opened bias sweep file:" + result)
                tab.bias_sweep_file_toolbar_enabled = True
                if not self.update_bias_sweep_plot_from_file(ch_id):
                    self.close_bias_sweep_file(ch_id)

    def update_bias_sweep_plot_from_file(self, ch_id: int) -> bool:
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
            self._queue_param(ch_id, val, p.method)
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
            self._queue_param(ch_id, val, ch_tab.chan.vna.center.method)
        self.change_float_param(ch_id, ch_tab.chan.pump_source.frequency)
