
class UnableToConnectError(Exception):
    def __init__(self, msg: str):
        self.msg = msg


class ChIndexOutOfRange(Exception):
    def __init__(self, msg: str):
        self.msg = msg
