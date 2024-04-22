import pyvisa as visa
from typing import Any
from anti_qsweepy.drivers import exceptions


class Instrument:
    def parse_on_off_val(self, val: Any) -> str:
        if val is not None:
            if type(val) is bool:
                if val: return "1"
                else: return "0"
            elif val not in ["on", "off", "ON", "OFF", "1", "0", 1, 0]:
                raise ValueError("Argument must be bool or either of [\"ON\",\"OFF\",\"1\",\"0\",1,0]")
            if val in [1, 0]:
                val = str(val)
            elif val.upper() == "ON":
                val = "1"
            else:
                val = "0"
        return val


class VisaInstrument(Instrument):
    """Base class for VISA instruments that use SCPI-style syntax."""
    def __init__(self, address, term_chars=None):
        self.address = address
        self.term_chars = term_chars
        self.always_query = False
        self.n_trys = 5
        self._open_instrument()

    def _open_instrument(self):
        try:
            self.instr = visa.ResourceManager().open_resource(self.address)
        except visa.VisaIOError as err:
            msg = "%s (%d): %s" % (err.abbreviation, err.error_code, err.description)
            raise exceptions.UnableToConnectError(msg)
        if self.term_chars is not None:
            self.instr.write_termination = self.term_chars
            self.instr.read_termination = self.term_chars

    def _visa_transfer(self, act: str, cmd: str) -> str:
        res = None
        if act == 'write':
            self.instr.write(cmd)
        elif act == 'read':
            res = self.instr.read(cmd)
        elif act == 'query':
            res = self.instr.query(cmd)
        return res

    def _safe_visa_transfer(self, act: str, cmd: str) -> str:
        try:
            res = self._visa_transfer(act, cmd)
        except visa.VisaIOError as e:
            if e.error_code in [visa.errors.VI_ERROR_TMO, visa.errors.VI_ERROR_CONN_LOST]:
                print("Connection to the instrument {:s} lost, trying to reconnect...".format(self.address))
                for i in range(self.n_trys):
                    try:
                        self._open_instrument()
                        print("Reconnected successfully")
                        break
                    except:
                        if i == self.n_trys - 1:
                            raise
                        else:
                            print("Try {:d}: failed to reconnect".format(i + 1))
                res = self._visa_transfer(act, cmd)
            else:
                raise
        if res is not None:
            return res

    def write(self, cmd: str) -> None:
        self._safe_visa_transfer('write', cmd)

    def read(self, cmd: str) -> str:
        return self._safe_visa_transfer('read', cmd)

    def query(self, cmd: str) -> str:
        return self._safe_visa_transfer('query', cmd)

    # Uneversal parameter access. If no val specified it will query and return or write instead
    def write_or_query(self, message, val=None, fmt_str="{:d}"):
        if val is not None:
            if self.always_query:
                val = self.instr.query(message + " " + fmt_str.format(val))
            else:
                self.instr.write(message + " " + fmt_str.format(val))
            return val
        else:
            return self.instr.query(message + "?")

    # Standard SCPI commands
    # Query instrument id string
    def idn(self):
        return self.instr.query("*IDN?")

    def close(self):
        self.instr.close()


class VisaInstrumentTSP(VisaInstrument):
    """Base class for VISA instruments that use
    Test Script Processor (TSP) instead of a normal SCPI syntax."""

    def write_or_query(self, message, val=None, fmt_str="{:d}"):
        if val is not None:
            self.instr.write(message + " = " + fmt_str.format(val))
            return val
        else:
            return self.instr.query('print({:s})'.format(message))
