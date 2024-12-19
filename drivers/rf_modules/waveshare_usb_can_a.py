import serial
from enum import IntEnum

class CAN_SPEED(IntEnum):
    SPEED_1000000 = 1000000
    SPEED_800000 = 800000
    SPEED_500000 = 500000
    SPEED_400000 = 400000
    SPEED_250000 = 250000
    SPEED_200000 = 200000
    SPEED_125000 = 125000
    SPEED_100000 = 100000
    SPEED_50000 = 50000
    SPEED_20000 = 20000
    SPEED_10000 = 10000
    SPEED_5000 = 5000

CAN_SPEED_CODE = {  1000000: 0x01,
                    800000: 0x02,
                    500000: 0x03,
                    400000: 0x04,
                    250000: 0x05,
                    200000: 0x06,
                    125000: 0x07,
                    100000: 0x08,
                    50000: 0x09,
                    20000: 0xA0,
                    10000: 0xB0,
                    5000: 0xC0}

class COM_BAUDRATE(IntEnum):
    BAUDRATE_2000000 = 2000000
    BAUDRATE_122880 = 122880
    BAUDRATE_115200 = 115200
    BAUDRATE_38400 = 38400
    BAUDRATE_19200 = 19200
    BAUDRATE_9600 = 9600

class CANUSB_MODE(IntEnum):
    NORMAL = 0x00
    LOOPBACK = 0x01
    SILENT = 0x02
    LOOPBACK_SILENT = 0x03

class CAN_FRAME_SIZE(IntEnum):
    STANDARD = 0x01
    EXTENDED = 0x02

class CAN_FRAME_TYPE(IntEnum):
    DATA = 0x01
    REMOTE = 0x02

class CAN_RETRANSMISSION(IntEnum):
    ENABLED = 0x00
    DISABLED = 0x01

class SERIAL_DATA_TYPE(IntEnum):
    FIXED_20_BYTES_SETUP = 0x02
    FIXED_20_BYTES_DATA = 0x01
    FLEXIBLE_SETUP =0x12
    FLEXIBLE_DATA = 0xC0

SERIAL_DATA_SIZE = 20


class WaveshareUSB_CAN_A:
    def __init__(self, com_port:str,
                 baudrate:int, can_speed: int,
                 frame_size: CAN_FRAME_SIZE = CAN_FRAME_SIZE.STANDARD,
                 mode: CANUSB_MODE = CANUSB_MODE.NORMAL,
                 timeout: float = 1):

        self.frame_size = frame_size
        if baudrate % can_speed:
            raise Exception("COM baud rate must be divisible by CAN speed")
        self.dev = serial.Serial(com_port, baudrate)
        self.dev.timeout = timeout
        self.timeout = timeout
        self._setup(can_speed, frame_size, mode)

    def _setup(self, can_speed: int,
                    frame_size: CAN_FRAME_SIZE,
                    mode: CANUSB_MODE) -> None:
        """Set up the adapter"""

        frame = bytearray()
        frame.extend([0xaa, 0x55])
        frame.append(SERIAL_DATA_TYPE.FIXED_20_BYTES_SETUP)
        frame.append(CAN_SPEED_CODE[can_speed])
        frame.append(frame_size)
        frame.extend([0] * 8)  # Fill with zeros for Filter ID and Mask ID (not handled)
        frame.append(mode)
        frame.append(CAN_RETRANSMISSION.ENABLED)
        frame.extend([0, 0, 0, 0])
        frame.append(self._checksum(frame))
        self.dev.write( bytes(frame) )

    def __del__(self):
        self.dev.close()

    def close(self) -> None:
        self.dev.close()

    @staticmethod
    def _checksum(data: bytearray) -> int:
        checksum = sum( data[2:SERIAL_DATA_SIZE-1] )
        return checksum & 0xff

    def send(self, can_id:int, data:bytes) -> None:
        frame = bytearray()
        frame.extend([0xaa,0x55])
        frame.append(SERIAL_DATA_TYPE.FIXED_20_BYTES_DATA)
        frame.append(self.frame_size)
        frame.append(CAN_FRAME_TYPE.DATA)

        if self.frame_size is CAN_FRAME_SIZE.STANDARD:
            if can_id > 2**11-1:
                raise Exception("Standard CAN ID is 11 bits and can not exceed 0x7FF, got {0}".format(can_id))
            frame.extend( can_id.to_bytes(2, 'little') )
            frame.extend([0,0])
        elif self.frame_size is CAN_FRAME_SIZE.EXTENDED:
            if can_id > 2**29-1:
                raise Exception("Standard CAN ID is 11 bits and can not exceed 0x1fffffff, got {0}".format(can_id))
            frame.extend(can_id.to_bytes(4, 'little'))

        length = len(data)
        if length > 8:
            raise Exception("CAN data length can not exceed 8 bytes, got {0}".format(length))
        frame.append(length)

        frame.extend(data)
        frame.extend([0]*(8-length))
        frame.append(0x00)
        frame.append( self._checksum(frame) )
        self.dev.timeout = self.timeout
        self.dev.write( bytes(frame) )

    def receive(self) -> tuple[int,bytes] | tuple[None, None]:
        self.dev.timeout = self.timeout
        resp = self.dev.read( SERIAL_DATA_SIZE )
        if len(resp):
            can_id = int.from_bytes( resp[5:9], 'little' )
            length = resp[9]
            #print(resp)
            #print(length)
            data = resp[10:10+length]
            return can_id, data
        return None, None
