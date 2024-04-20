import sys
import multiprocessing as mp


class StdOutputCatcher:
    def __init__(self, q: mp.Queue, ui_ch: int):
        self.ui_ch = ui_ch
        self.q = q
        self._stdout = None

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, type, value, traceback):
        sys.stdout = self._stdout

    def write(self, msg: str) -> None:
        self.q.put({'op': 'log_push', 'args': (msg, self.ui_ch)})
