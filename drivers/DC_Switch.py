from anti_qsweepy.drivers.instrument_base_classes import VisaInstrument


class DC_Switch(VisaInstrument):
    def __init__(self, *args, **kwargs):
        VisaInstrument.__init__(self, *args, term_chars="\n", **kwargs)
        self._positions = 12

    def state(self, val=None):
        if val is not None:
            if len(val) != self._positions:
                raise ValueError('Number of positions must be equal to {:d}!'.format(self._positions))
            sw_list = 'STAT '
            for i, v in enumerate(val):
                if v:
                    sw_list += '1'
                else:
                    sw_list += '0'
                if i + 1 < len(val):
                    sw_list += ','
            self.instr.query(sw_list)
        else:
            val = [int(str) for str in self.instr.query('STAT?').split(',')]
        return val

    def set(self, chan, state):
        return (self.instr.query("CHAN{:d} {:s}".format(int(chan), state)))
