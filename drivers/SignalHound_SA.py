import numpy as np
from anti_qsweepy.drivers.signal_hound import _signal_hound
import ctypes


def get_signal_hounds():
    serial_numbers, num_devices = _signal_hound.get_serial_number_list()
    devices = [s for s in serial_numbers[:num_devices]]
    return devices


class SpectrumAnalyzer():
    '''
    This is the python driver for the Signal Hound SA124 spectrum analyzer
    '''

    def __init__(self, serial):
        '''
        Initializes

        Input:
            serial (int) : serial number
        '''
        self._device = _signal_hound.open_device_by_serial_number(serial_number=serial)
        self.serial = serial

        self.reject_if = True
        self.res_bw = _signal_hound.max_rbw
        self.video_bw = _signal_hound.max_rbw
        self.averages = 1

        _signal_hound.config_sweep_coupling(self._device, self.res_bw, self.video_bw, self.reject_if)
        _signal_hound.initiate(self._device, _signal_hound.sweeping, 0)
        # Detector
        _signal_hound.config_acquisition(self._device, _signal_hound.average, _signal_hound.log_scale)
        # Units
        _signal_hound.config_proc_units(self._device, _signal_hound.power_units)
        # Window shape
        _signal_hound.config_rbw_shape(self._device, _signal_hound.rbw_shape_cispr)

        self.reference_level = _signal_hound.max_ref
        self.ref_level(self.reference_level)

    def soft_trig_arm(self):
        pass

    def soft_trig_abort(self):
        pass

    def read_data(self):
        '''
        Get the data of the current trace in W
        '''
        _signal_hound.initiate(self._device, _signal_hound.sweeping, 0)
        nop, start_freq, bin_size = _signal_hound.query_sweep_info(self._device)

        min = (ctypes.c_float * nop)()
        max = (ctypes.c_float * nop)()
        datamin = np.zeros(nop)
        # datamax = np.zeros(nop)
        if self.averages == 0:
            averages = 1
        else:
            averages = self.averages
        for _ in range(averages):
            end = 0
            while end < nop:
                begin, end = _signal_hound.get_partial_sweep_32f(self._device, min, max)
            datamin += 10. ** (np.asarray(min, dtype=np.float) / 10.)
        #	datamax += 10.**(np.asarray(min, dtype=np.float)/10.)

        # datax = np.linspace(start_freq, start_freq+bin_size*(nop-1), nop)
        datamin = 1e-3 * datamin / averages
        # datamax = datamax/self.averages

        return datamin

    def _adjust_bw(self, bw):

        _signal_hound.initiate(self._device, _signal_hound.sweeping, 0)
        nop, start_freq, bin_size = _signal_hound.query_sweep_info(self._device)
        span = (nop - 1) * bin_size

        bw_6MHz_allowed = False
        bw_max = 250e3
        bw_min = _signal_hound.min_rbw
        if span > 100e6:
            bw_min = 6.5e3
        if span > 200e3 and start_freq < 16e6:
            bw_min = 6.5e3
        if start_freq > 200e6 and span > 200e6:
            bw_6MHz_allowed = True

        if bw > bw_max:
            if bw_6MHz_allowed and bw > 3e6:
                bw = 6e6
            else:
                bw = bw_max

        if bw < bw_min:
            bw = bw_min
        return bw

    def rbw(self, val=None):
        '''
        Resolution bandwidth
        '''
        if val is not None:
            self.res_bw = self._adjust_bw(val)
            if self.video_bw > self.res_bw:
                self.video_bw = self.res_bw
            _signal_hound.config_sweep_coupling(self._device, self.res_bw, self.video_bw, self.reject_if)
        return self.res_bw

    def vbw(self, val=None):
        '''
        Video bandwidth
        '''
        if val is not None:
            self.video_bw = self._adjust_bw(val)
            if self.video_bw > self.res_bw:
                self.video_bw = self.res_bw
            _signal_hound.config_sweep_coupling(self._device, self.res_bw, self.video_bw, self.reject_if)
        return self.video_bw

    def ref_level(self, val=None):
        if val is not None:
            self.reference_level = val
            _signal_hound.config_level(self._device, val)
        return self.reference_level

    def freq_start_stop(self, val):
        _signal_hound.initiate(self._device, _signal_hound.sweeping, 0)
        if val is not None:
            _signal_hound.config_center_span(self._device, (val[0] + val[1]) / 2, val[1] - val[0])
        else:
            nop, start_freq, bin_size = _signal_hound.query_sweep_info(self._device)
            if nop < 2: nop = 2
            val = [0, 0]
            val[0] = start_freq
            val[1] = start_freq + (nop - 1) * bin_size
        return val

    def freq_center_span(self, val):
        _signal_hound.initiate(self._device, _signal_hound.sweeping, 0)
        if val is not None:
            _signal_hound.config_center_span(self._device, val[0], val[1])
        else:
            nop, start_freq, bin_size = _signal_hound.query_sweep_info(self._device)
            if nop < 2: nop = 2
            stop_freq = start_freq + (nop - 1) * bin_size
            val = [0, 0]
            val[0] = (start_freq + stop_freq) / 2.
            val[1] = stop_freq - start_freq
        return val

    '''		
    def freq_start(self, val=None):
        _signal_hound.initiate(self._device, _signal_hound.sweeping, 0)
        nop, start_freq, bin_size = _signal_hound.query_sweep_info(self._device)
        if val is not None:
            if nop<2: nop = 2
            print("start ",start_freq)
            stop_freq = start_freq + (nop-1)*bin_size
            if stop_freq < val:
                span = 1e6
                center_freq = val+span/2
            else:
                center_freq = (val+stop_freq)*0.5
                span = stop_freq - val
            _signal_hound.config_center_span(self._device, center_freq,  span)
            return val
        return start_freq
        
    def freq_stop(self, val=None):
        _signal_hound.initiate(self._device, _signal_hound.sweeping, 0)
        nop, start_freq, bin_size = _signal_hound.query_sweep_info(self._device)
        if val is not None:
            center_freq = (val+start_freq)*0.5
            span = val - start_freq
            _signal_hound.config_center_span(self._device, center_freq, span)
            return val
        if nop<2: nop = 2
        return start_freq + (nop-1)*bin_size
        
    def freq_center(self, val=None):
        _signal_hound.initiate(self._device, _signal_hound.sweeping, 0)
        nop, start_freq, bin_size = _signal_hound.query_sweep_info(self._device)
        if nop<2: nop = 2
        stop_freq = start_freq + (nop-1)*bin_size
        if val is not None:
            _signal_hound.config_center_span(self._device, val, stop_freq-start_freq)
            return val
        return (start_freq+stop_freq)/2.
        
    def freq_span(self, val=None):
        _signal_hound.initiate(self._device, _signal_hound.sweeping, 0)
        nop, start_freq, bin_size = _signal_hound.query_sweep_info(self._device)
        if nop<2: nop = 2
        stop_freq = start_freq + (nop-1)*bin_size
        if val is not None:
            _signal_hound.config_center_span(self._device, (start_freq + stop_freq)*0.5, val)
            return val
        return stop_freq-start_freq
    '''

    def freq_points(self):
        _signal_hound.initiate(self._device, _signal_hound.sweeping, 0)
        nop, start_freq, bin_size = _signal_hound.query_sweep_info(self._device)
        return np.linspace(start_freq, start_freq + bin_size * (nop - 1), nop)

    def averaging(self, val=None):
        if val is not None:
            self.averages = val
        return self.averages
