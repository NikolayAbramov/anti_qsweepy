import re
import http.client
from anti_qsweepy.drivers.TemperatureControllerBaseClass import *


class TemperatureController(TemperatureControllerBaseClass):
    """Temperature controller interface implemented via Artiom's Bluefors parameter exporter
    running on the cryostat control PC"""
    def __init__(self, address: str):
        tokens = address.split(":")
        self.host = tokens[0]
        self.port = int(tokens[1])
        self.conn = http.client.HTTPConnection(self.host, self.port)

    def temperature(self, chan: int) -> float:
        """Returns temperature at the channel chan. Channels are remapped by Artiom and do not
        correspond to the original Bluefors mapping. Channel ids: 1 - PT1, 2 - PT2, 3 - Still, 4 - MC."""
        if chan > 4 or chan < 1:
            raise ValueError("Channel id is out of range!")
        self.conn.request("GET", "/metrics", headers={"Host": self.host})
        resp = self.conn.getresponse()
        body = str(resp.read(), encoding='utf-8')
        tokens = re.split(' |\n', body)
        return float(tokens[chan*2-1])
