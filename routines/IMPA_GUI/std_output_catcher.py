import sys
import multiprocessing as mp

class StdOutputCatcher:
    def __init__(self, q: mp.Queue, ui_ch: int):
        self.ui_ch = ui_ch
        self.q = q
        self._stdout = None
        self._buf = ''

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, type, value, traceback):
        sys.stdout = self._stdout

    def write(self, msg: str) -> None:
        self._buf += msg
        if msg[-1] == '\n':
            self.flush()

    def flush(self):
        self.q.put({'op': 'log_push', 'args': (self._buf, self.ui_ch)})
        self._buf = ''
