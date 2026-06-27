"""Single channel wrappers for multiple channels instruments"""
import warnings

class SingleChannelBiasSource:
    """Single channel wrappers for bias source"""
    __slots__ = ('device','_ch',)
    def __init__(self, device, ch:int):
        self.device = device
        self.device.channel(ch)
        self._ch = ch

    def channel(self, val: int = None) -> int:
        """Sets active channel"""
        if val is not None:
            if val:
                warnings.warn(f"Single channel wrapper has only channel 0, got {val} instead")
        return 0

    def setpoint(self, val: float | None = None) -> float:
        self.device.channel(self._ch)
        return self.device.setpoint(val)

    def output(self, val: str| bool | None = None) -> bool:
        self.device.channel(self._ch)
        return self.device.output(val)

    def limit(self, val: float | None = None, ch:int|None = None) -> float:
        self.device.channel(self._ch)
        return self.device.limit(val)

    def range(self, val: float | None = None, ch:int|None = None) -> float:
        self.device.channel(self._ch)
        return self.device.range(val)

    def autorange(self, val: bool | None = None, ch:int|None = None) -> bool:
        self.device.channel(self._ch)
        return self.device.autorange(val)