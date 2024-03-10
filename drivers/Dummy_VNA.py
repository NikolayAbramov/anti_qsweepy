# Network alnalyzer simulation model
import numpy as np
import numpy.typing as npt
import time
from typing import Any


class NetworkAnalyzer:

    def __init__(self, *args):
        self._power = 0
        self._bandwidth = 1000
        self._center = 7e9
        self._span = 1e9
        self._f_cw = 7e9
        self._points = 500
        self._averaging = 1
        self._period = 0.5e9
        self._output = False
        self._sw_type = 'LIN'
        self._attr = 0

    def _query_or_write(self, attr_name: str, val: Any = None) -> Any:
        if val is not None:
            setattr(self, attr_name, val)
        return getattr(self, attr_name)

    def soft_trig_arm(self) -> None:
        pass

    def read_data(self) -> np.ndarray:
        time.sleep(self._points / self._bandwidth)
        x = self.freq_points()
        r_offset = 0.01
        data = (np.sin(2 * np.pi * x / self._period) + 1 + r_offset +
                1.j * np.cos(2 * np.pi * x / self._period)) / (2 + r_offset)
        return data

    def soft_trig_abort(self) -> None:
        pass

    def power(self, val: float = None) -> float:
        return self._query_or_write('_power', val)

    def bandwidth(self, val: float = None) -> float:
        return self._query_or_write('_bandwidth', val)

    def freq_start_stop(self, val: tuple[float, float] = None) -> tuple[float, float]:
        if val is not None:
            self._center = (val[0] + val[1]) / 2
            self._span = val[1] - val[0]
        return self._center - self._span / 2, self._center + self._span / 2

    def freq_center_span(self, val: tuple[float, float] = None) -> tuple[float, float]:
        if val is not None:
            self._center = val[0]
            self._span = val[1]
        return self._center, self._span

    def freq_cw(self, val: float = None) -> float:
        return self._query_or_write('_f_cw', val)

    def num_of_points(self, val: int = None) -> int:
        return self._query_or_write('_points', val)

    def output(self, val:bool = None) -> bool:
        self._query_or_write('_output', val)
        return self._output

    def freq_points(self) -> npt.NDArray[float]:
        f_points = np.linspace(self._center - self._span / 2,
                               self._center + self._span / 2,
                               self._points)
        return f_points

    def sweep_type(self, val:str = None) -> str:
        if val is not None:
            val = val.upper()
            if val.upper() not in ['SEGM', 'LIN', 'CW']:
                raise ValueError("Argument must be either of [\"SEGM\",\"LIN\",\"CW]")
            self._sw_type = val
        return self._sw_type

    def seg_tab(self, seg_tab):
        #TODO implement segment table support
        pass

    def averaging(self, val:int = None) -> int:
        return self._query_or_write('averaging', val)

    def close(self):
        pass