# Network alnalyzer
from numpy import *
from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument
import time


class NetworkAnalyzer(VisaInstrument):

    def __init__(self, *args):
        VisaInstrument.__init__(self, *args)
        self.instr.write("CALC:PAR:MNUM 1")
        self.instr.write('FORM REAL,32; FORM:BORD SWAP;')
        self.instr.write('SENS:AVER:MODE POIN')
        self._abort = False
        self._ch = 0

    def channel(self, val=None):
        """Set active channel. There is only one channel 0 on this device."""
        if val is not None:
            if val != self._ch:
                raise ValueError('There is only one channel 0 on this device!')
        return self._ch

    def abort(self) -> None:
        """Abort read_data() thread"""
        self._abort = True

    def soft_trig_arm(self):
        self.instr.write("TRIG:SOUR MAN")
        self.instr.write("*ESE 1")
        self.instr.write("SENS:AVER:MODE POIN")

    def read_data(self):
        # Clear status, initiate measurement
        self.instr.write("*CLS")
        self.instr.write("INIT:IMM")
        self.instr.write("*OPC")
        # Set bit in ESR when operation complete
        while int(self.instr.query("*ESR?")) == 0:
            if self._abort:
                self._abort = False
                return array(())
            time.sleep(0.002)
        data = self.instr.query_binary_values("CALC:DATA? SDATA", datatype=u'f')
        data_size = size(data)
        return array(data[0:data_size:2]) + 1.j * array(data[1:data_size:2])

    def soft_trig_abort(self):
        self.instr.write("ABOR")
        self.instr.write("TRIG:SOUR IMM")

    def power(self, val=None):
        return float(self.write_or_query("SOUR:POW", val, "{:f}"))

    def bandwidth(self, val=None):
        return int(self.write_or_query("SENS1:BAND", val, "{:f}"))

    def freq_start_stop(self, val=None):
        if val is not None:
            self.instr.write("SENS1:FREQ:START {:e}".format(val[0]))
            self.instr.write("SENS1:FREQ:STOP {:e}".format(val[1]))
        else:
            val = [0, 0]
            val[0] = float(self.instr.query("SENS1:FREQ:START?"))
            val[1] = float(self.instr.query("SENS1:FREQ:STOP?"))
        return val

    def freq_center_span(self, val=None):
        if val is not None:
            self.instr.write("SENS1:FREQ:CENT {:e}".format(val[0]))
            self.instr.write("SENS1:FREQ:SPAN {:e}".format(val[1]))
        else:
            val = [0, 0]
            val[0] = float(self.instr.query("SENS1:FREQ:CENT?"))
            val[1] = float(self.instr.query("SENS1:FREQ:SPAN?"))
        return val

    def freq_cw(self, val=None):
        return float(self.write_or_query("SENS1:FREQ:CW", val, "{:e}"))

    def num_of_points(self, val=None):
        return int(self.write_or_query("SENS1:SWE:POIN", val, "{:d}"))

    def output(self, val=None):
        val = self.write_or_query('OUTP', self.parse_on_off_val(val), "{:s}")
        if val == '1':
            return True
        else:
            return False

    def freq_points(self):
        return array(self.instr.query_binary_values('SENS1:X?', datatype=u'f'))

    def sweep_type(self, val=None):
        if val is not None:
            val = val.upper()
            if val.upper() not in ['SEGM', 'LIN', 'CW', 'POW', 'LOG']:
                raise ValueError("Argument must be either of [\"SEGM\",\"LIN\",\"CW]")
        return self.write_or_query("SENS1:SWE:TYPE", val, "{:s}")

    def seg_tab(self, seg_tab):
        # Segment description format:
        # {'start':0, 'stop':0, 'points':0, 'power':0,'bandwidth':0}
        # SegTable = '{:d}'.format(len(seg_tab))

        # for seg in seg_tab:
        #	SegTable += ',1,{:d}'.format( int(seg['points'] ) )
        #	SegTable += ',{:e},{:e},{:e}'.format( seg['start'], seg['stop'], seg['Bandwidth'] )

        self.instr.write("SENS1:SEGM:DEL:ALL")
        self.instr.write("SENS1:SEGM:BWID:CONT ON")
        self.instr.write("SENS1:SEGM:POW:CONT ON")
        for i, seg in enumerate(seg_tab):
            n = i + 1
            self.instr.write("SENS1:SEGM{:d}:ADD".format(n))
            self.instr.write("SENS:SEGM{:d}:BWID {:f}".format(n, seg['bandwidth']))
            self.instr.write("SENS:SEGM{:d}:POW {:f}".format(n, seg['power']))
            self.instr.write("SENS:SEGM{:d}:FREQ:START {:f}".format(n, seg['start']))
            self.instr.write("SENS:SEGM{:d}:FREQ:STOP {:f}".format(n, seg['stop']))
            self.instr.write("SENS:SEGM{:d}:SWE:POIN {:d}".format(n, seg['points']))
            self.instr.write("SENS:SEGM{:d} ON".format(n))

    # self.instr.write("SENS1:SEGM:LIST SSTOP,"+SegTable)

    def averaging(self, val=None):
        # TODO insrt proper commands (these are from ZNB20)
        if val is not None:
            if val > 1:
                self.instr.write('SENS:AVER:STAT ON')
                self.instr.write('SENS:AVER:COUN {:d}'.format(val))
            else:
                self.instr.write('SENS:AVER:STAT OFF')
        else:
            if int(self.instr.query('SENS:AVER:STAT?')):
                val = int(self.instr.query('SENS:AVER:COUN?'))
            else:
                val = 0
        return val
