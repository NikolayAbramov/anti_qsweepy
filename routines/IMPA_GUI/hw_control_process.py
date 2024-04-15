import multiprocessing as mp
import traceback as tb
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Any

import anti_qsweepy.drivers as drv
from bias_sweep import BiasSweepParameters, BiasSweep


def hw_process(q_command: mp.Queue, q_feedback: mp.Queue) -> None:
    """ Hardware control process
    """
    hwcp = HWCommandProcessor(q_feedback)
    print("HW process started")
    try:
        while True:
            command = q_command.get(block=True)
            if command['op'] != 'get_vna_data':
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


@dataclass
class PhyDevice:
    """Physical device class

    Attributes:
        driver_name (str): Device driver name within the anti_qsweepy.drivers module
        class_name (str): Device class name within the driver
        chan (int): Associated physical device channel
        dev_inst: Device class instance
        similar_ui_ch (list): List of UI channels sharing the same device with the
                              same driver_name and associated physical channel"""
    driver_name: str
    class_name: str
    chan: int
    dev_inst: Any
    similar_ui_ch: list[int]


@dataclass
class BiasSource(PhyDevice):
    dev_inst: drv.Dummy_CurrentSource.CurrentSource


@dataclass
class PumpSource(PhyDevice):
    dev_inst: drv.Dummy_Generator.Generator


@dataclass
class VNA(PhyDevice):
    dev_inst: drv.Dummy_VNA.NetworkAnalyzer

@dataclass
class VNAReadDataFuture:
    """VNA data acquisition thread future
    """
    future: Future
    ui_ch: int


class HWCommandProcessor:
    def __init__(self, q_feedback: mp.Queue):
        self.q = q_feedback
        # Physical devices bind to a particular UI channel identified by int channel id keys
        self.vna: dict[int, VNA] = {}
        self.bias_source: dict[int, BiasSource] = {}
        self.pump_source: dict[int, PumpSource] = {}
        # Executor for multiple threads
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.vna_read_data_future: Future | None = None  # VNA data acquisition thread
        self.bias_sweeps: dict[int, BiasSweep] = {}

    def _connect_device(self, device_dict: dict[int, PhyDevice],
                        driver_name: str,
                        class_name: str,
                        address: str,
                        ch: int,
                        ui_ch: int) -> tuple[bool,list[int]]:
        existing_phy_device = None
        existing_dev_inst = None
        affected_ui_ch = [ui_ch]
        similar_ui_ch = [ui_ch]
        for existing_ui_ch in device_dict.keys():
            phy_dev = device_dict[existing_ui_ch]
            if phy_dev.driver_name == driver_name:
                affected_ui_ch += [existing_ui_ch]
                if phy_dev.chan == ch:
                    similar_ui_ch += [existing_ui_ch]
                    existing_phy_device = phy_dev
                existing_dev_inst = phy_dev.dev_inst
        if existing_phy_device is not None:
            if existing_phy_device.dev_inst is None:
                existing_phy_device.dev_inst = self._connect_instr(driver_name, class_name, address)
            existing_phy_device.similar_ui_ch = similar_ui_ch
            device_dict.update({ui_ch: existing_phy_device})
            if existing_phy_device.dev_inst is None:
                return False, affected_ui_ch
            return True, affected_ui_ch
        else:
            if existing_dev_inst is None:
                existing_dev_inst = self._connect_instr(driver_name, class_name, address)
            if existing_dev_inst is None:
                return False, affected_ui_ch
            if ui_ch not in device_dict.keys():
                phy_device = PhyDevice(driver_name=driver_name,
                                        class_name=class_name,
                                        dev_inst=existing_dev_inst,
                                        chan=ch,
                                        similar_ui_ch=similar_ui_ch)
                device_dict.update({ui_ch: phy_device})
                return True, affected_ui_ch
            for ui_ch in affected_ui_ch:
                device_dict[ui_ch].dev_inst = existing_dev_inst
        return True, affected_ui_ch

    def _connect_instr(self, driver_name: str, class_name: str, address: str) -> Any:
        try:
            driver = getattr(drv, driver_name)
            DeviceClass = getattr(driver, class_name)
            return DeviceClass(address)
        except Exception:
            tb.print_exc()
            return None

    def _disconnect_device(self, device_dict: dict[int, PhyDevice],
                           ui_ch: int) -> list[int]:
        ui_ch_list = []
        if ui_ch in device_dict.keys():
            ui_ch_list = [ui_ch]
            driver_name = device_dict[ui_ch].driver_name
            for existing_ui_ch in device_dict.keys():
                phy_dev = device_dict[existing_ui_ch]
                if phy_dev.driver_name == driver_name:
                    ui_ch_list += [existing_ui_ch]
                    if phy_dev.dev_inst is not None:
                        try:
                            phy_dev.dev_inst.close()
                            phy_dev.dev_inst = None
                        except Exception:
                            tb.print_exc()
        return ui_ch_list

    def _stop_read_data_if_running(self, ui_ch: int):
        phy_dev = self.vna[ui_ch]
        """Check vna.read_data thread and stop if running"""
        if self.vna_read_data_future is not None:
            if self.vna_read_data_future.running():
                phy_dev.dev_inst.abort()

    def connect_pump_source(self, driver_name: str, class_name: str, address: str, ch: int, ui_ch: int) -> None:
        status, ui_ch_list = self._connect_device(self.pump_source, driver_name, class_name, address, ch, ui_ch)
        if status:
            for ui_ch in ui_ch_list:
                self.q.put({'op': 'connect_pump_source', 'args': (ui_ch,)})
        else:
            for ui_ch in ui_ch_list:
                self.q.put({'op': 'disconnect_pump_source', 'args': (ui_ch,)})

    def disconnect_pump_source(self, ui_ch: int) -> None:
        ui_ch_list = self._disconnect_device(self.pump_source, ui_ch)
        for ui_ch in ui_ch_list:
            self.q.put({'op': 'disconnect_pump_source', 'args': (ui_ch,)})

    def set_pump_output(self,val: bool, ui_ch: int) -> None:
        phy_dev = self.pump_source[ui_ch]
        phy_dev.dev_inst.channel(phy_dev.chan)
        val = phy_dev.dev_inst.output(val)
        self.q.put({'op': 'set_pump_output', 'args': (val, ui_ch)})

    def set_pump_power(self, val:float, ui_ch: int) -> None:
        phy_dev = self.pump_source[ui_ch]
        phy_dev.dev_inst.channel(phy_dev.chan)
        val = phy_dev.dev_inst.power(val)
        self.q.put({'op': 'set_pump_power', 'args': (val, ui_ch)})

    def set_pump_frequency(self, val:float, ui_ch: int) -> None:
        phy_dev = self.pump_source[ui_ch]
        phy_dev.dev_inst.channel(phy_dev.chan)
        val = phy_dev.dev_inst.freq(val)
        self.q.put({'op': 'set_pump_frequency', 'args': (val, ui_ch)})

    def connect_bias_source(self, driver_name: str, class_name: str, address: str, ch: int, ui_ch: int) -> None:
        status, ui_ch_list = self._connect_device( self.bias_source, driver_name, class_name, address, ch, ui_ch)
        if status:
            for ui_ch in ui_ch_list:
                self.q.put({'op': 'connect_bias_source', 'args': (ui_ch,)})
        else:
            for ui_ch in ui_ch_list:
                self.q.put({'op': 'disconnect_bias_source', 'args': (ui_ch,)})

    def disconnect_bias_source(self, ui_ch: int) -> None:
        status, ui_ch_list = self._disconnect_device(self.bias_source, ui_ch)
        for ui_ch in ui_ch_list:
            self.q.put({'op': 'disconnect_bias_source', 'args': (ui_ch,)})

    def set_bias_current(self, val: float, ui_ch: int) -> None:
        phy_dev = self.bias_source[ui_ch]
        phy_dev.dev_inst.channel(phy_dev.chan)
        val = phy_dev.dev_inst.setpoint(val)
        self.q.put({'op': 'set_bias_current', 'args': (val, ui_ch)})

    def set_bias_limit(self, val: float, ui_ch: int) -> None:
        phy_dev = self.bias_source[ui_ch]
        phy_dev.dev_inst.channel(phy_dev.chan)
        val = phy_dev.dev_inst.limit(val)
        self.q.put({'op': 'set_bias_limit', 'args': (val, ui_ch)})

    def set_bias_output(self, val: bool,  ui_ch: int) -> None:
        phy_dev = self.bias_source[ui_ch]
        phy_dev.dev_inst.channel(phy_dev.chan)
        val = phy_dev.dev_inst.output(val)
        self.q.put({'op': 'set_bias_output', 'args': (val, ui_ch)})

    def connect_vna(self, driver_name: str, class_name: str, address: str, ch: int, ui_ch: int):
        status, ui_ch_list = self._connect_device(self.vna, driver_name, class_name, address, ch, ui_ch)
        for ui_ch in ui_ch_list:
            if status:
                self.q.put({'op': 'connect_vna', 'args': (ui_ch,)})
            else:
                self.q.put({'op': 'disconnect_vna', 'args': (ui_ch,)})

    def disconnect_vna(self, ui_ch: int) -> None:
        ui_ch_list = self._disconnect_device(self.vna, ui_ch)
        for ui_ch in ui_ch_list:
            self.q.put({'op': 'disconnect_vna', 'args': (ui_ch,)})

    def set_vna_power(self, val: float, ui_ch: int) -> None:
        if ui_ch in self.vna.keys():
            phy_dev = self.vna[ui_ch]
            self._stop_read_data_if_running(ui_ch)
            phy_dev.dev_inst.channel(phy_dev.chan)
            phy_dev.dev_inst.power(val)
            for ui_ch in phy_dev.similar_ui_ch:
                self.q.put({'op': 'set_vna_power', 'args': (val, ui_ch)})

    def set_vna_bandwidth(self, val: float, ui_ch: int) -> None:
        if ui_ch in self.vna.keys():
            phy_dev = self.vna[ui_ch]
            self._stop_read_data_if_running(ui_ch)
            phy_dev.dev_inst.channel(phy_dev.chan)
            phy_dev.dev_inst.bandwidth(val)
            for ui_ch in phy_dev.similar_ui_ch:
                self.q.put({'op': 'set_vna_bandwidth', 'args': (val, ui_ch)})

    def set_vna_points(self, val: int, ui_ch: int) -> None:
        if ui_ch in self.vna.keys():
            phy_dev = self.vna[ui_ch]
            self._stop_read_data_if_running(ui_ch)
            phy_dev.dev_inst.channel(phy_dev.chan)
            phy_dev.dev_inst.num_of_points(val)
            for ui_ch in phy_dev.similar_ui_ch:
                self.q.put({'op': 'set_vna_points', 'args': (val, ui_ch)})

    def set_vna_center(self, val: float, ui_ch: int) -> None:
        if ui_ch in self.vna.keys():
            phy_dev = self.vna[ui_ch]
            self._stop_read_data_if_running(ui_ch)
            phy_dev.dev_inst.channel(phy_dev.chan)
            center, span = phy_dev.dev_inst.freq_center_span()
            phy_dev.dev_inst.freq_center_span( (val,span ) )
            for ui_ch in phy_dev.similar_ui_ch:
                self.q.put({'op': 'set_vna_center', 'args': (val, ui_ch)})

    def set_vna_span(self, val: float, ui_ch: int) -> None:
        if ui_ch in self.vna.keys():
            phy_dev = self.vna[ui_ch]
            self._stop_read_data_if_running(ui_ch)
            phy_dev.dev_inst.channel(phy_dev.chan)
            center, span = phy_dev.dev_inst.freq_center_span()
            phy_dev.dev_inst.freq_center_span((center, val))
            for ui_ch in phy_dev.similar_ui_ch:
                self.q.put({'op': 'set_vna_span', 'args': (val, ui_ch)})

    def _get_vna_data(self, ui_ch):
        if ui_ch in self.vna.keys():
            phy_dev = self.vna[ui_ch]
            freq_points = phy_dev.dev_inst.freq_points()
            S21 = 20*np.log10(np.abs(phy_dev.dev_inst.read_data()))
            data = np.vstack((freq_points, S21))
            self.q.put({'op': 'update_gain_plot', 'args': (data, ui_ch)})

    def get_vna_data(self, ui_ch) -> None:
        if ui_ch in self.vna.keys():
            phy_dev = self.vna[ui_ch]
            if self.vna_read_data_future is None:
                self.vna_read_data_future = self.executor.submit(self._get_vna_data, ui_ch)
            elif not self.vna_read_data_future.running():
                self.vna_read_data_future = self.executor.submit(self._get_vna_data, ui_ch)

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