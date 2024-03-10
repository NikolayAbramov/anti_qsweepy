from numpy import *
from typing import Any


class CurrentSource:
    """Current source with differential outputs"""
    def __init__(self, *args):
        self._n_ch: int = 12
        self._ch: int = 0
        self._setpoint: list[float] = [0]*self._n_ch
        self._output: list[bool] = [False]*self._n_ch
        self._limit: list[float] = [1] * self._n_ch
        self._range: list[float] = [10e-3] * self._n_ch
        self._autorange: list[bool] = [False]*self._n_ch

    def _query_or_write(self, attr_name: str, val: Any) -> Any:
        if val is not None:
            getattr(self, attr_name)[self._ch] = val
        return getattr(self, attr_name)[self._ch]

    def channel(self, val=None):
        """Set active channel"""
        if val is not None:
            self._ch = val
        return self._ch

    def channels(self) -> int:
        return self._n_ch

    def setpoint(self, val: float = None) -> float:
        return self._query_or_write('_setpoint', val)

    def output(self, val: bool = None) -> bool:
        return self._query_or_write('_output', val)

    def limit(self, val: float = None) -> float:
        return self._query_or_write('_limit', val)

    def range(self, val: float = None) -> float:
        return self._query_or_write('_range', val)

    def autorange(self, val: bool = None) -> bool:
        return self._query_or_write('_autorange', val)
