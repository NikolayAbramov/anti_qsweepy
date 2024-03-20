import multiprocessing as mp
import traceback as tb
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import Future

import anti_qsweepy.drivers as drv
from anti_qsweepy.routines import data_mgmt
from bias_sweep import BiasSweepParameters, BiasSweep

def hw_process(q_command: mp.Queue, q_feedback: mp.Queue) -> None:
    """ Hardware control process
    """
    hwcp = HWCommandProcessor(q_feedback)
    print("HW process started")
    try:
        while True:
            command = q_command.get(block=True)
            print("HW process got command: ", command['op'], command['args'])
            if command['op'] == 'terminate':
                break
            try:
                getattr(hwcp, command['op'])(*command['args'])
            except Exception as err:
                tb.print_exc()
    except KeyboardInterrupt:
        pass
    print("HW process terminated")


class HWCommandProcessor:
    def __init__(self, q_feedback: mp.Queue):
        self.q = q_feedback
        self.vna: drv.Dummy_VNA.NetworkAnalyzer | None = None
        self.bias_source: drv.Dummy_CurrentSource.CurrentSource | None = None
        self.pump_source: drv.Dummy_Generator.Generator | None = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.vna_data_future: Future|None = None
        self.bias_sweeps: dict[int,BiasSweep] = {}

    def _connect_device(self, device_inst_name: str,
                        driver_name: str,
                        class_name: str,
                        address: str,
                        ch_id: int) -> None:
        device_inst = getattr(self, device_inst_name)
        if device_inst is None:
            driver = getattr(drv, driver_name)
            DeviceClass = getattr(driver, class_name)
            setattr(self, device_inst_name, DeviceClass(address))
        device_inst = getattr(self, device_inst_name)
        if device_inst is not None:
            self.q.put({'op': 'connect_'+device_inst_name, 'args': (ch_id,)})
        else:
            self.q.put({'op': 'disconnect_'+device_inst_name, 'args': (ch_id,)})

    def _disconnect_device(self, device_inst_name: str,
                           ch_id: int) -> None:
        device_inst = getattr(self, device_inst_name)
        if device_inst is not None:
            device_inst.close()
            setattr(self, device_inst_name, None)
        self.q.put({'op': 'disconnect_'+device_inst_name, 'args': (ch_id,)})

    def _stop_read_data_if_running(self):
        """Check vna.read_data thread and stop if running"""
        if self.vna_data_future is not None:
            if self.vna_data_future.running():
                self.vna.abort()

    def connect_pump_source(self, driver_name: str, class_name: str, address: str, ch_id: int) -> None:
        self._connect_device('pump_source', driver_name, class_name, address, ch_id)

    def disconnect_pump_source(self, ch_id):
        self._disconnect_device('pump_source', ch_id)

    def set_pump_output(self,val: bool, ch_id:int) -> None:
        self.pump_source.channel(ch_id)
        val = self.pump_source.output(val)
        self.q.put({'op': 'set_pump_output', 'args': (val, ch_id)})

    def set_pump_power(self, val:float, ch_id: int) -> None:
        self.pump_source.channel(ch_id)
        val = self.pump_source.power(val)
        self.q.put({'op': 'set_pump_power', 'args': (val, ch_id)})

    def set_pump_frequency(self, val:float, ch_id: int) -> None:
        self.pump_source.channel(ch_id)
        val = self.pump_source.freq(val)
        self.q.put({'op': 'set_pump_frequency', 'args': (val, ch_id)})

    def connect_bias_source(self, driver_name: str, class_name: str, address: str, ch_id: int) -> None:
        self._connect_device('bias_source', driver_name, class_name, address, ch_id)

    def disconnect_bias_source(self, ch_id: int) -> None:
        self._disconnect_device('bias_source', ch_id)

    def set_bias_current(self, val: float, ch_id: int) -> None:
        self.bias_source.channel(ch_id)
        val = self.bias_source.setpoint(val)
        self.q.put({'op': 'set_bias_current', 'args': (val,ch_id)})

    def set_bias_limit(self, val: float, ch_id: int) -> None:
        self.bias_source.channel(ch_id)
        val = self.bias_source.limit(val)
        self.q.put({'op': 'set_bias_limit', 'args': (val, ch_id)})

    def set_bias_output(self, val: bool,  ch_id: int) -> None:
        self.bias_source.channel(ch_id)
        val = self.bias_source.output(val)
        self.q.put({'op': 'set_bias_output', 'args': (val, ch_id)})

    def connect_vna(self, driver_name: str, class_name: str, address: str, ch_id: int):
        self._connect_device('vna', driver_name, class_name, address, ch_id)

    def disconnect_vna(self, ch_id):
        self._disconnect_device('vna', ch_id)

    def set_vna_power(self, val: float, ch_id: int) -> None:
        self.vna.power(val)
        self.q.put({'op': 'set_vna_power', 'args': (val,ch_id)})

    def set_vna_bandwidth(self, val: float, ch_id: int) -> None:
        self._stop_read_data_if_running()
        self.vna.bandwidth(val)
        self.q.put({'op': 'set_vna_bandwidth', 'args': (val, ch_id)})

    def set_vna_points(self, val: int, ch_id: int) -> None:
        self.vna.num_of_points(val)
        self.q.put({'op': 'set_vna_points', 'args': (val, ch_id)})

    def set_vna_center(self, val: float, ch_id: int) -> None:
        center, span = self.vna.freq_center_span()
        self.vna.freq_center_span( (val,span ) )
        self.q.put({'op': 'set_vna_center', 'args': (val, ch_id)})

    def set_vna_span(self, val: float, ch_id: int) -> None:
        center, span = self.vna.freq_center_span()
        self.vna.freq_center_span((center, val))
        self.q.put({'op': 'set_vna_span', 'args': (val, ch_id)})

    def _get_vna_data(self, ch_id):
        if self.vna is not None:
            freq_points = self.vna.freq_points()
            S21 = 20*np.log10(np.abs(self.vna.read_data()))
            data = np.vstack((freq_points, S21))
            self.q.put({'op': 'update_gain_plot', 'args': (data,ch_id)})


    def get_vna_data(self, ch_id) -> None:
        #if self.vna is not None:
        #    freq_points = self.vna.freq_points()
        #    S21 = 20*np.log10(np.abs(self.vna.read_data()))
        #    data = np.vstack((freq_points, S21))
        #    self.q.put({'op': 'update_gain_plot', 'args': (data,ch_id)})
        if self.vna_data_future is None:
            self.vna_data_future = self.executor.submit(self._get_vna_data, ch_id)
        elif not self.vna_data_future.running():
            self.vna_data_future = self.executor.submit(self._get_vna_data, ch_id)

    def start_bias_sweep(self, data: dict) -> None:
        if data['ch_id'] in self.bias_sweeps.keys():
            if self.bias_sweeps[data['ch_id']].future.running():
                return
        parameters = BiasSweepParameters(**data)
        bs = BiasSweep(self.bias_source, self.vna, self.q, parameters)
        bs.future = self.executor.submit(bs.sweep)
        self.bias_sweeps.update({data['ch_id']: bs})
        self.q.put({'op': 'start_bias_sweep', 'args': (data['ch_id'],)})

    def abort_bias_sweep(self, ch_id) -> None:
        if ch_id in self.bias_sweeps.keys():
            if self.bias_sweeps[ch_id].future.running():
                self.bias_sweeps[ch_id].abort()
        self.q.put({'op': 'stop_bias_sweep', 'args': (ch_id,)})
