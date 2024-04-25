from typing import Any


class Generator:
    def __init__(self, *args):
        self._n_ch = 4
        self._ch = 0
        self._args = [{'power': 0,
                       'frequency': 5e9,
                       'output': False}]*self._n_ch

    def _query_or_write(self, attr_name: str, val: Any) -> Any:
        if val is not None:
            self._args[self._ch][attr_name] = val
        return self._args[self._ch][attr_name]

    def channels(self):
        return self._n_ch

    def channel(self, val = None):
        return self._query_or_write('_ch', val)

    def close(self):
        pass

    def power(self, val: float = None) -> float:
        return self._query_or_write('power', val)

    def freq(self, val: float = None) -> float:
        return self._query_or_write('frequency', val)

    def phase(self, val: float = None) -> float:
        return self._query_or_write('phase', val)

    def output(self, val: bool = None) -> bool:
        return self._query_or_write('output', val)