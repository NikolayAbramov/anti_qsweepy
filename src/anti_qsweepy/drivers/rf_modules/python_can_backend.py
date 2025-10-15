import can

class PythonCAN_GS_USB_Backend:
    def __init__(self, filters:dict):
        self.timeout = 1
        filters['extended'] = False
        filters = [filters,]
        self.bus = can.Bus(interface="gs_usb", channel=0x606F, index=0, bitrate=500000, can_filters=filters)

    def send(self, can_id: int, data: bytes ) -> None:
        msg = can.Message(arbitration_id=can_id, data=data, is_extended_id=False)
        self.bus.send(msg, timeout=self.timeout)

    def receive(self) -> tuple[int,bytes] | tuple[None, None]:
        msg = self.bus.recv(timeout=self.timeout)
        if msg is not None:
            return msg.arbitration_id, msg.data
        return None, None

    def __del__(self):
        self.bus.shutdown()
        self.bus.gs_usb.gs_usb.reset()