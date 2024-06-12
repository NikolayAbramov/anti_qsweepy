# -*- coding: utf-8 -*-
"""
Added upon by Bridgette McAllister, SignalCore 7/8/2022
---
Created on Fri Mar 19 14:11:31 2021
Adapted from Chao Zhou
---
A simple driver for SignalCore SC5511A, transferred from the one written by Erick Brindock
"""

import ctypes
from typing import Any, Dict, Optional
import numpy as np
from pprint import pprint
from anti_qsweepy.drivers.instrument_base_classes import Instrument
from anti_qsweepy.drivers.signal_core.sc5511a import SignalCore_SC5511A
import anti_qsweepy.drivers.signal_core.sc5511a as sc
from anti_qsweepy.drivers import exceptions


class Generator(Instrument):
    """An abstract RF generator class for SignalCore SC5511A."""
    def __init__(self, serial_number: str,
                 dll_path: str = 'C:\\Program Files\\SignalCore\\SC5511A\\api\\c\\x64\\sc5511a.dll', debug=False,
                 **kwargs: Any):
        self._dll_path = dll_path
        self._serial_numbers = []
        for s in serial_number.replace(' ', '').split(','):
            self._serial_numbers += [bytes(s, 'utf-8')]
        print(self._serial_numbers)
        self._dll = ctypes.WinDLL(dll_path)
        self._dll.sc5511a_open_device.restype = ctypes.c_uint64
        buf = []
        for i in range(10):
            buf += [ctypes.create_string_buffer(8)]
        arr = (ctypes.c_void_p * 10)(*map(ctypes.addressof, buf))
        self._dll.sc5511a_search_devices(arr)
        serial_numbers_found = []
        for val in buf:
            serial_numbers_found += [val.value]
        for s in self._serial_numbers:
            if s not in serial_numbers_found:
                raise exceptions.UnableToConnectError('Serial number {0} for SignalCore SC5511A not found'.format(s))
        # Activate channel 0 by default
        self._ch = 0
        self._handle = ctypes.c_void_p(self._dll.sc5511a_open_device(ctypes.c_char_p(self._serial_numbers[self._ch])))
        self._clock_config = sc.Clock_config_t(0, 0, 0, 0, 0)
        self._rf_params = sc.Device_rf_params_t(0, 0, 0, 0, 0, 0, 0, 0, 0)
        self._status = sc.Operate_status_t(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self._phase = sc.Phase_t(0)
        self._temperature = sc.Device_temperature_t(0)
        self._dac_value = sc.Dac_value_t(0)
        self._freq = sc.List_buffer_set_t(0)
        self._reg_read = sc.Reg_read_t(0)
        self._pll_status = sc.Pll_status_t()
        self._list_mode = sc.List_mode_t()
        self._manufacture_date = sc.Manufacture_date_t(0, 0, 0, 0)
        self._device_status = sc.Device_status_t(self._list_mode, self._status, self._pll_status)
        if debug:
            print(self._serial_numbers, self._handle)
            self._dll.sc5511a_get_device_status(self._handle, ctypes.byref(self._device_status))
            status = self._device_status.operate_status_t.rf1_out_enable
            print('check status', status)

        self._device_info = sc.Device_info_t(0, 0, 0, self._manufacture_date)

    def close(self) -> None:
        """closes the device session"""
        self._dll.sc5511a_close_device(self._handle)

    def preset(self) -> None:
        pass

    def channels(self) -> int:
        """Return number of channels."""
        return len(self._serial_numbers)

    def channel(self, val: int | None = None) -> int:
        """Set active channel."""
        if val is not None:
            if val >= len(self._serial_numbers) or val < 0:
                raise ValueError('Channel index {0} is out of range'.format(val))
            if val != self._ch:
                self._ch = val
                self.close()
                self._handle = ctypes.c_void_p(self._dll.sc5511a_open_device(ctypes.c_char_p(
                    self._serial_numbers[self._ch])))
        return self._ch

    def output(self, val: bool | None = None) -> bool:
        """
        Turns the output of RF1 on or off or gets its state.
            Input: bool
        """
        if val is not None:
            val = int(self.parse_on_off_val(val))
            c_enable = ctypes.c_ubyte(val)
            error_code = self._dll.sc5511a_set_output(self._handle, c_enable)
            return bool(val)
        else:
            error_code = self._dll.sc5511a_get_device_status(self._handle, ctypes.byref(self._device_status))
            val = bool(self._device_status.operate_status_t.rf1_out_enable)
        return val

    def freq(self, val: float | None = None) -> float:
        """
        Sets or gets RF1 frequency. Valid between 100MHz and 20GHz
            Args:
                val (int) = frequency in Hz
        """
        if val is not None:
            val = int(np.round(val))
            c_freq = ctypes.c_ulonglong(int(val))
            error_code = self._dll.sc5511a_set_freq(self._handle, c_freq)
        else:
            error_code = self._dll.sc5511a_get_rf_parameters(self._handle, ctypes.byref(self._rf_params))
            val = float(self._rf_params.rf1_freq)
        return val

    def power(self, val: float | None = None) -> float:
        """Sets or gets the power level
            val: float dBm
        """
        if val is not None:
            c_power = ctypes.c_float(val)
            error_code = self._dll.sc5511a_set_level(self._handle, c_power)
        else:
            error_code = self._dll.sc5511a_get_rf_parameters(self._handle, ctypes.byref(self._rf_params))
            val = self._rf_params.rf_level
        return val

    def phase(self, val: float | None = None) -> float:
        """Sets or gets the signal phase of the device
            input: float"""
        if val is not None:
            c_phase = ctypes.c_float(val)
            error_code = self._dll.sc5511a_set_signal_phase(self._handle, c_phase)
        else:
            error_code = self._dll.sc5511a_get_signal_phase(self._handle, ctypes.byref(self._phase))
            val = self._phase.phase
        return val
