class Artificial_SMU():
    def __init__(self, source_inst, meter_inst):
        self.source_inst = source_inst
        self.meter_inst = meter_inst
        self.source_type = 'CURRENT'
        self.four_wire_state = 'ON'

    def four_wire(self, val=None):
        # On - 4-wire, Off - 2-wire
        if val is None:
            return self.four_wire_state
        else:
            self.four_wire_state = val
            return val

    def source(self, val=None):
        if val is None:
            return self.source_type
        else:
            self.source_type = val
            return val

    def output(self, val=None):
        return self.source_inst.output(val)

    def setpoint(self, val=None):
        return self.source_inst.setpoint(val)

    def read_data(self):
        return self.meter_inst.read_data()

    def limit(self, val=None):
        return self.source_inst.limit(val)

    def source_range(self, val=None):
        return self.source_inst.range(val)

    def meter_range(self, val=None):
        return self.meter_inst.range(val)

    def source_autorange(self, val=None):
        return self.source_inst.autorange(val)

    def meter_autorange(self, val=None):
        return self.meter_inst.autorange(val)

    def aperture(self, val=None):
        return self.meter_inst.aperture(val)

    def averaging_count(self, val=None):
        return self.meter_inst.averaging_count(val)

    def close(self):
        self.source_inst.close()
        self.meter_inst.close()
