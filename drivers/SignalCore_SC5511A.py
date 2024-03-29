
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
from pprint import pprint
from anti_qsweepy.drivers.instrument_base_classes import Instrument


class Device_rf_params_t(ctypes.Structure):
    _fields_ = [("rf1_freq", ctypes.c_ulonglong),   #current ch#1 rf frequency
                ("start_freq", ctypes.c_ulonglong), #list start frequency
                ("stop_freq", ctypes.c_ulonglong),  #list stop frequency (>start_freq)
                ("step_freq", ctypes.c_ulonglong),  #list step frequency
                ("sweep_dwell_time", ctypes.c_uint),    #dwell time at each frequency
                ("sweep_cycles", ctypes.c_uint),    #number of cycles to sweep/list
                ("buffer_points", ctypes.c_uint),   #current number of list buffer points
                ("rf_level", ctypes.c_float),   #current ch#1 power level
                ("rf2_freq", ctypes.c_short)    #current ch#2 rf frequency
                ]

class Phase_t(ctypes.Structure):
    _fields_ = [("phase", ctypes.c_float)]

class Device_temperature_t(ctypes.Structure):
    _fields_ = [("device_temp", ctypes.c_float)]

class Dac_value_t(ctypes.Structure):
    _fields_ = [("dac_value", ctypes.c_ushort)]

class List_buffer_t(ctypes.Structure):
    _fields_ = [("transfer_mode", ctypes.c_ubyte)]

class List_buffer_set_t(ctypes.Structure):
    _fields_ = [("device_freq", ctypes.c_ulonglong)]

class Reg_read_t(ctypes.Structure):
    _fields_ = [("reg_read", ctypes.c_ulonglong)]


class Operate_status_t(ctypes.Structure):
    _fields_ = [("rf1_lock_mode", ctypes.c_ubyte),  #synthesizer lock mode for chn#1: 0 = use harmonic curcuit, 1 = fracN circuit
                ("rf1_loop_gain", ctypes.c_ubyte),  #changing the loop gain of the sum pll. 0 = normal, 1 = low. Low gain helps suppress spurs and far out phase noise, but increases the close in phase
                ("device_access", ctypes.c_ubyte),  #if a session has been open for the device
                ("rf2_standby", ctypes.c_ubyte),    #indicates chn#2 standby and output disable
                ("rf1_standby", ctypes.c_ubyte),    #indicates chn#1 standby
                ("auto_pwr_disable", ctypes.c_ubyte),   #indicates power adjustment is performed when frequency is changed
                ("alc_mode", ctypes.c_ubyte),   #indicates alc behavior: 0 is closed, 1 is open
                ("rf1_out_enable", ctypes.c_ubyte), #indicates chn#1 RF output
                ("ext_ref_lock_enable", ctypes.c_ubyte),    #indicates that 100 MHz VCXO is set to lock to an external source
                ("ext_ref_detect", ctypes.c_ubyte), #indicates external source detected
                ("ref_out_select", ctypes.c_ubyte), #indicates the reference output select: 0 = 10 MHz, 1 = 100 MHz
                ("list_mode_running", ctypes.c_ubyte),  #indicates list/sweep is triggered and currently running
                ("rf1_mode", ctypes.c_ubyte),   #indicates chn#1 rf mode set: 0=fixed tone state, 1 = list/sweep mode state
                ("harmonic_ss", ctypes.c_ubyte),    #harmonic spur suppression state
                ("over_temp", ctypes.c_ubyte)   #indicates if the temperature of the devices has exceeded ~75 deg C internally
                ]


class Pll_status_t(ctypes.Structure):
    _fields_ = [("sum_pll_ld", ctypes.c_ubyte), #lock status of main pll loop
                ("crs_pll_ld", ctypes.c_ubyte), #lock status of coarse offset pll loop (used only for harmonic mode)
                ("fine_pll_ld", ctypes.c_ubyte),    #lock status of the dds tuned fine pll loop
                ("crs_ref_pll_ld", ctypes.c_ubyte), #lock status of the coarse reference pll loop
                ("crs_aux_pll_ld", ctypes.c_ubyte), #lock status of the auxiliary coarse pll loop (used only for IntN or FracN mode)
                ("ref_100_pll_ld", ctypes.c_ubyte), #lock status of the 100 MHz VCXO pll loop
                ("ref_10_pll_ld", ctypes.c_ubyte),  #lock status of the master 10 MHz TCXO pll loop
                ("rf2_pll_ld", ctypes.c_ubyte)] #lock status of the chn#2 pll loop


class List_mode_t(ctypes.Structure):
    _fields_ = [("sss_mode", ctypes.c_ubyte),   #0 uses list for buffer, 1 calculates using stop-start-step 
                ("sweep_dir", ctypes.c_ubyte),  #0 start/beginning to stop/end, 1 stop/end to start/beginning
                ("tri_waveform", ctypes.c_ubyte),   #0 sawtooth, 1 triangular
                ("hw_trigger", ctypes.c_ubyte),     #0 soft trigger expected, 1 hard trigger expected
                ("step_on_hw_trig", ctypes.c_ubyte),    #0 trigger to sweep through list, 1 stepping on every trigger (on hard trigger only)
                ("return_to_start", ctypes.c_ubyte),    #if 1, frequency returns to start frequency after end of cycle(s)
                ("trig_out_enable", ctypes.c_ubyte),    #1 enables a trigger pulse at the trigger on pin
                ("trig_out_on_cycle", ctypes.c_ubyte)]  #0 trigger out on every frequency change, 1 trigger on cycle complete


class Device_status_t(ctypes.Structure):
    _fields_ = [("list_mode", List_mode_t), #list mode parameters
                ("operate_status_t", Operate_status_t), #operating parameters
                ("pll_status_t", Pll_status_t)] #pll status

class Manufacture_date_t(ctypes.Structure):
    _fields_ = [("year", ctypes.c_ubyte),
                ("month", ctypes.c_ubyte),
                ("day", ctypes.c_ubyte),
                ("hour", ctypes.c_ubyte)]

class Device_info_t(ctypes.Structure):
    _fields_ = [("serial_number", ctypes.c_uint32),
                ("hardware_revision", ctypes.c_float),
                ("firmware_revision", ctypes.c_float),
                ("manufacture_date", Manufacture_date_t)
                ]

class Clock_config_t(ctypes.Structure):
    _fields_ = [("ext_ref_lock_enable", ctypes.c_ubyte),    #select to lock to either external reference source
                ("ref_out_select", ctypes.c_ubyte),     #select either 10 or 100 MHz output
                ("pxi_clock_enable", ctypes.c_ubyte),   #
                ("ext_direct_clocking", ctypes.c_ubyte),    #enable direct 100 MHz clocking of the synthesizer, bypassing its internal 100 MHz clock
                ("ext_ref_freq", ctypes.c_ubyte)]   #selects the input frequency


# End of Structures------------------------------------------------------------

"""An abstract generator"""
class Generator(Instrument):
    def __init__(self, serial_number: str, dll_path: str = 'C:\\Program Files\\SignalCore\\SC5511A\\api\\c\\x64\\sc5511a.dll', debug = False, **kwargs: Any):

        self._dll = ctypes.WinDLL(dll_path)

        if debug:
            print(self._dll)

        self._dll.sc5511a_open_device.restype = ctypes.c_uint64
        self._handle = ctypes.c_void_p(self._dll.sc5511a_open_device(ctypes.c_char_p(bytes(serial_number, 'utf-8'))))
        
        self._serial_number = ctypes.c_char_p(bytes(serial_number, 'utf-8'))
        self._clock_config = Clock_config_t(0, 0, 0, 0, 0)
        self._rf_params = Device_rf_params_t(0, 0, 0, 0, 0, 0, 0, 0, 0)
        self._status = Operate_status_t(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self._phase = Phase_t(0)
        self._temperature = Device_temperature_t(0)
        self._dac_value = Dac_value_t(0)
        self._freq = List_buffer_set_t(0)
        self._reg_read = Reg_read_t(0)
        self._pll_status = Pll_status_t()
        self._list_mode = List_mode_t()
        self._manufacture_date = Manufacture_date_t(0, 0, 0, 0)
        self._device_status = Device_status_t(self._list_mode, self._status, self._pll_status)
        if debug:
            print(serial_number, self._handle)
            self._dll.sc5511a_get_device_status(self._handle, ctypes.byref(self._device_status))
            status = self._device_status.operate_status_t.rf1_out_enable
            print('check status', status)

        self._device_info = Device_info_t(0, 0, 0, self._manufacture_date)

    def _close(self):
        """closes the device session"""
        self._dll.sc5511a_close_device(self._handle)
        
    def preset(self):
        pass

    def output(self, val = None):
        """
        Turns the output of RF1 on or off or gets its state.
            Input:
                val = ON/OFF or 1/0 str or int
        """
        if val is not None:
            val = int( self.parse_on_off_val(val) )
            c_enable = ctypes.c_ubyte(val)
            error_code = self._dll.sc5511a_set_output(self._handle, c_enable)
        else:
            error_code = self._dll.sc5511a_get_device_status(self._handle, ctypes.byref(self._device_status))
            val = self._device_status.operate_status_t.rf1_out_enable
        return val
        
         
    def freq(self, val=None):
        """
        Sets or gets RF1 frequency. Valid between 100MHz and 20GHz
            Args:
                val (int) = frequency in Hz
        """
        if val is not None:
            val = int(val)
            c_freq = ctypes.c_ulonglong(int(val))
            error_code = self._dll.sc5511a_set_freq(self._handle, c_freq)
        else:
            error_code = self._dll.sc5511a_get_rf_parameters(self._handle, ctypes.byref(self._rf_params))
            val = self._rf_params.rf1_freq
        return val
        
        
    def power(self, val = None):
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

    def phase(self, val = None):
        """Sets or gets the signal phase of the device
            input: float"""
        if val is not None:
            c_phase= ctypes.c_float(phase)
            error_code = self._dll.sc5511a_set_signal_phase(self._handle, c_phase)
        else:
            error_code = self._dll.sc5511a_get_signal_phase(self._handle, ctypes.byref(self._phase))
            val = self._phase.phase
        return val

