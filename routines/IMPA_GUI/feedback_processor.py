import data_structures as ds
import multiprocessing as mp
import traceback as tb
import numpy.typing as nt
from typing import Any
import numpy as np

class FeedbackProcessor:
    def __init__(self, q_feedback: mp.Queue, ui_objects: ds.UiObjects):
        self.ui_objects = ui_objects
        self.q_feedback = q_feedback

    def set_pump_output(self, val: bool, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.pump_source.output, val)

    def set_pump_power(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.pump_source.power, val)

    def set_pump_frequency(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.pump_source.frequency, val)

    def connect_pump_source(self, ch_id: int) -> None:
        pass

    def connect_bias_source(self, ch_id: int) -> None:
        pass

    def disconnect_bias_source(self, ch_id: int) -> None:
        pass

    def set_bias_current(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.bias_source.current, val)

    def set_bias_output(self, val: bool, ch_id: int):
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.bias_source.output, val)

    def connect_vna(self, ch_id:int):
        tab = self.ui_objects.channel_tabs[ch_id]
        tab.chan.vna.is_connected.update(True)
        tab.chan.vna.set_parameters_enable(True)
        tab.chan.vna.is_connected.enabled = True

    def disconnect_vna(self, ch_id):
        tab = self.ui_objects.channel_tabs[ch_id]
        tab.chan.vna.is_connected.update(False)
        tab.chan.vna.set_parameters_enable(False)
        tab.chan.vna.is_connected.enabled = True

    def set_vna_power(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.vna.power, val)

    def set_vna_bandwidth(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.vna.bandwidth, val)

    def set_vna_points(self, val: int, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.vna.points, val)

    def set_vna_center(self, val: float, ch_id: int) -> None:
        vna = self.ui_objects.channel_tabs[ch_id].chan.vna
        vna.center.update(val)
        if not vna.pump_center_bind.value:
            vna.center.enabled = True

    def set_vna_span(self, val: float, ch_id: int) -> None:
        self._update_param(self.ui_objects.channel_tabs[ch_id].chan.vna.span, val)

    def update_gain_plot(self, data: nt.ArrayLike, ch_id: int) -> None:
        data = np.array(data)
        tab = self.ui_objects.channel_tabs[ch_id]
        fig = tab.gain_fig
        trace_id = self.ui_objects.gain_plot_traces.vna_s21
        fig['data'][trace_id]['x'] = list(data[0]/1e9)
        fig['data'][trace_id]['y'] = list(data[1])
        fig['data'][trace_id]['name'] = 'VNA S21'
        tab.gain_plot.update()

    def _update_param(self, p: ds.UIParameter, val: Any):
        p.update(val)
        p.enabled = True

    def check_queue(self) -> None:
        if not self.q_feedback.empty():
            command = self.q_feedback.get()
            if command['op'] != "update_gain_plot":
                print("Main process got feedback: ", command['op'],command['args'])
            else:
                print("Main process got feedback: ", command['op'])
            try:
                getattr(self, command['op'])(*command['args'])
            except Exception as err:
                tb.print_exc()
