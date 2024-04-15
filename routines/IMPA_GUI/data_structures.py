from dataclasses import dataclass, field, fields
from nicegui import ui
from typing import Any
import hdf5_gain
import hdf5_bias_sweep
from numpy.typing import ArrayLike
import numpy as np


@dataclass
class UIParameter:
    """Base class for parameters bind to UI inputs"""
    name:       str = "UI parameter"
    method:     str = "set_parameter"
    str_repr:   str = '0'
    enabled:    bool = True
    value:      Any = None
    instrumental: bool = True

    def update_str(self) -> None:
        """Should update self.str_repr from self.value"""
        pass

    def update_val(self) -> None:
        """Should update  self.value from self.str_repr"""
        pass

    def update(self, val: Any) -> None:
        """Should update self.value with new one and also
         update self.str_repr"""
        self.value = val
        self.update_str()

    def get_value(self) -> Any:
        """Should produce conditioned value from self.str_repr"""
        return self.value


@dataclass
class FloatUIParam(UIParameter):
    """Floating point parameter associated with UI input"""
    value:      float = 0
    step:       float = 0.001
    precision:  float | None = 0.001
    unit:       float = 1
    min:        float | None = 0
    max:        float | None = 1
    str_fmt:    str = '{:.3f}'
    step_sel:   dict = field(default_factory=
                             lambda: {0.1: '0.100',0.01: '0.010',0.001: '0.001'})

    def update_str(self) -> None:
        """Updates string representation"""
        self.str_repr = self.str_fmt.format(self.value/self.unit)

    def update_val(self) -> None:
        self.value = self.get_value()
        self.update_str()

    def update(self, val: float) -> None:
        """Updates value and string representation"""
        self.value = val
        self.update_str()

    def get_value(self) -> float:
        """Converts string representation into a conditioned value"""
        try:
            val = float(self.str_repr)
        except ValueError:
            self.update_str()
            return self.value
        if self.max is not None:
            if val > self.max:
                return self.max * self.unit
        if self.min is not None:
            if val < self.min:
                return self.min * self.unit
        if self.precision is not None:
            return round(val / self.precision) * self.precision * self.unit
        return val*self.unit

    def inc(self):
        """Returns incremented value"""
        val = self.value + self.step * self.unit
        if self.max is not None:
            val_max = self.max*self.unit
            if val > val_max:
                return val_max
        return val

    def dec(self):
        """Returns decremented value"""
        val = self.value - self.step * self.unit
        if self.min is not None:
            val_min = self.min*self.unit
            if val < val_min and val_min is not None:
                return val_min
        return val

@dataclass
class BoolUIParameter(UIParameter):
    """Bool parameter associated with some UI control"""
    value:      bool = False
    str_true:   str = 'On'
    str_false:  str = 'Off'

    def update_str(self) -> None:
        if self.value:
            self.str_repr = self.str_true
        else:
            self.str_repr = self.str_false

    def update(self, val: bool) -> None:
        self.value = val
        self.update_str()

    def get_value(self) -> bool:
        return self.value


@dataclass
class Device:
    driver_name:    str = 'device'
    class_name:     str = 'Device'
    address:        str = 'device_address'
    channel:        int = 0
    connect_method: str = 'connect_device'
    disconnect_method: str = 'disconnect_device'
    is_connected: BoolUIParameter = field(default_factory=
                                       lambda: BoolUIParameter(
                                            instrumental=False,
                                            name='connected',
                                            method='device_connect',
                                            value=False,
                                            enabled=True,
                                            str_repr='Connect',
                                            str_true='Disconnect',
                                            str_false='Connect')
                                       )

    def set_parameters_enable(self, val: bool):
        """Enable or disable all the parameters except for
        self.is_connected"""
        for f in fields(self):
            if f.name != 'is_connected':
                attr = getattr(self, f.name)
                if hasattr(attr, 'enabled'):
                    attr.enabled = val


@dataclass
class VNA(Device):
    def __post_init__(self):
        self.is_connected.method = 'vna_connect'
        self.connect_method = 'connect_vna'
        self.disconnect_method = 'disconnect_vna'
    bandwidth: FloatUIParam = field(default_factory=
                                    lambda: FloatUIParam(name='Bandwidth, Hz',
                                                         method='set_vna_bandwidth',
                                                         precision = 1,
                                                         str_fmt='{:.0f}',
                                                         min=10,
                                                         max=100000))
    span: FloatUIParam = field(default_factory=
                               lambda: FloatUIParam(name='Span, GHz',
                                                    method='set_vna_span',
                                                    precision=0.001,
                                                    unit=1e9,
                                                    str_fmt='{:.3f}',
                                                    min=0.01,
                                                    max=10))
    center: FloatUIParam = field(default_factory=
                               lambda: FloatUIParam(name='Center, GHz',
                                                    method='set_vna_center',
                                                    precision=0.001,
                                                    unit=1e9,
                                                    str_fmt='{:.3f}',
                                                    min=0.01,
                                                    max=20))
    points: FloatUIParam = field(default_factory=
                               lambda: FloatUIParam(name='Points',
                                                    method='set_vna_points',
                                                    precision=1,
                                                    str_fmt='{:.0f}',
                                                    min=10,
                                                    max=10000))
    power: FloatUIParam = field(default_factory=
                               lambda: FloatUIParam(name='Power, dBm',
                                                    method='set_vna_power',
                                                    precision=0.1,
                                                    str_fmt='{:.1f}',
                                                    min=-100,
                                                    max=10))
    pump_center_bind: BoolUIParameter = field(default_factory=
                                              lambda: BoolUIParameter(name='Bind pump to vna center',
                                                                      value=False,
                                                                      enabled=True,
                                                                      instrumental=False))
    ref_data: np.ndarray[float, 2] | None = None
    normalize: BoolUIParameter = field(default_factory=
                                              lambda: BoolUIParameter(name='Normalize',
                                                                      value=False,
                                                                      enabled=True,
                                                                      instrumental=False))

@dataclass
class BiasSource(Device):
    def __post_init__(self):
        self.is_connected.method = 'bias_connect'
        self.connect_method = 'connect_bias_source'
        self.disconnect_method = 'disconnect_bias_source'
    output: BoolUIParameter = field(default_factory=
                                    lambda: BoolUIParameter(name='Output',
                                                            method='set_bias_output'))
    current: FloatUIParam = field(default_factory=
                                  lambda: FloatUIParam(name='Bias current, mA',
                                                       method='set_bias_current',
                                                       precision=0.001,
                                                       unit=1e-3,
                                                       str_fmt='{:.3f}',
                                                       min=-50,
                                                       max=50))
    compliance_voltage: FloatUIParam = field(default_factory=
                                             lambda: FloatUIParam(name='Compliance voltage',
                                                                  method='set_bias_limit',
                                                                  precision=0.1,
                                                                  unit=1,
                                                                  str_fmt='{:.1f}',
                                                                  min=0,
                                                                  max=50))


@dataclass
class PumpSource(Device):
    def __post_init__(self):
        self.is_connected.method = 'pump_connect'
        self.connect_method = 'connect_pump_source'
        self.disconnect_method = 'disconnect_pump_source'
    output: BoolUIParameter = field(default_factory=
                                    lambda: BoolUIParameter(name='Output',
                                                            method='set_pump_output'))
    power: FloatUIParam = field(default_factory=
                                lambda: FloatUIParam(name='Pump power, dBm',
                                                     method='set_pump_power',
                                                     precision=0.01,
                                                     unit=1,
                                                     str_fmt='{:.2f}',
                                                     min=-100,
                                                     max=30,
                                                     step_sel ={0.1: '0.10', 0.01: '0.01'},
                                                     step = 0.01
                                                     ))
    frequency: FloatUIParam = field(default_factory=
                                lambda: FloatUIParam(name='Pump frequency, GHz',
                                                     method='set_pump_frequency',
                                                     precision=0.001,
                                                     unit=1e9,
                                                     str_fmt='{:.3f}',
                                                     min=0.01,
                                                     max=50))

@dataclass
class BiasSweep:
    is_running: BoolUIParameter = \
        field(default_factory=
              lambda: BoolUIParameter(
                instrumental=False,
                name='running',
                method='',
                value=False,
                enabled=True,
                str_repr='Start',
                str_true='Stop',
                str_false='Start'
              ))
    bias_start: FloatUIParam = \
        field(default_factory=
              lambda: FloatUIParam(
                name='Bias start, mA',
                precision=0.001,
                unit=1e-3,
                str_fmt='{:.3f}',
                min=-50,
                max=50
                ))
    bias_stop: FloatUIParam = \
        field(default_factory=
              lambda: FloatUIParam(
                name='Bias stop, mA',
                precision=0.001,
                unit=1e-3,
                str_fmt='{:.3f}',
                min=-50,
                max=50
                ))
    bias_step: FloatUIParam = \
        field(default_factory=
              lambda: FloatUIParam(
                name='Bias step, mA',
                precision=0.001,
                unit=1e-3,
                str_fmt='{:.3f}',
                min=-50,
                max=50
                ))
    vna_start: FloatUIParam = \
        field(default_factory=
              lambda: FloatUIParam(
                name='VNA start, GHz',
                precision=0.001,
                unit=1e9,
                str_fmt='{:.3f}',
                min=-50,
                max=50
                ))
    vna_stop: FloatUIParam = \
        field(default_factory=
              lambda: FloatUIParam(
                name='VNA stop, GHz',
                precision=0.001,
                unit=1e9,
                str_fmt='{:.3f}',
                min=-50,
                max=50
                ))
    vna_power: FloatUIParam = \
        field(default_factory=
              lambda: FloatUIParam(
                name='VNA power, dBm',
                precision=0.01,
                unit=1,
                str_fmt='{:.2f}',
                min=-100,
                max=20
                ))
    vna_points: FloatUIParam = \
        field(default_factory=
              lambda: FloatUIParam(
                name='VNA points',
                precision=1,
                unit=1,
                str_fmt='{:.0f}',
                min=0,
                max=10000
                ))
    vna_bandwidth: FloatUIParam = \
        field(default_factory=
              lambda: FloatUIParam(
                name='VNA bandwidth, Hz',
                precision=1,
                unit=1,
                str_fmt='{:.0f}',
                min=1,
                max=1000000,
                value=10000
                ))
    save_path: str = ''
    progress: float = 0

    def set_parameters_enable(self, val: bool):
        """Enable or disable all the parameters except for
        self.is_connected"""
        for f in fields(self):
            if f.name != 'is_running':
                attr = getattr(self, f.name)
                if UIParameter in type(attr).mro():
                    attr.enabled = val

@dataclass
class Channel:
    """Channel related data"""
    name:           str = "Channel 0"
    vna:            VNA = field(default_factory=lambda: VNA())
    bias_source:    BiasSource = field(default_factory=lambda: BiasSource())
    pump_source:    PumpSource = field(default_factory=lambda: PumpSource())
    bias_sweep:     BiasSweep = field(default_factory=lambda: BiasSweep())


@dataclass
class GainPlotTraces:
    """Id-s of the gain plots traces."""
    vna_s21: int = 0
    vna_snr_gain: int = 1
    file_gain: int = 2
    file_snr_gain: int = 3

default_gain_fig_data = {   'type': 'scatter',
                            'name': 'Trace 1',
                            'x': [],
                            'y': []}

default_gain_fig ={'data': [{'type': 'scatter',
                             'name': 'Trace 1',
                             'x': [],
                             'y': []},
                            {'type': 'scatter',
                             'name': 'Trace 1',
                             'x': [],
                             'y': []},
                            {'type': 'scatter',
                             'name': 'Trace 1',
                             'x': [],
                             'y': []},
                            {'type': 'scatter',
                             'name': 'Trace 1',
                             'x': [],
                             'y': []},
                            ],
              'layout': {
                        'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
                        #'width': 350,
                        #'height':350,
                        #'plot_bgcolor': '#E5ECF6',
                        #'title':{'text':'Title'},
                        'annotations':[{'xanchor':'center',
                                        'yanchor':'bottom',
                                        'xref':'paper',
                                        'yref':'paper',
                                        'x':0.5,
                                        'y':0.01,
                                        'text':'',
                                        'showarrow':False,
                                        'bgcolor':'rgba(255,255,255,0.6)',
                                        'visible':True}],
                        'legend':{'visible':True,
                                  'x':0,
                                  'y':1, 
                                  'xanchor':'left',
                                  'yanchor':'top',
                                  'xref':'paper',
                                   'yref':'paper'},
                        'xaxis': {#'range':[0,5],
                                  'title':'Frequency, GHz',
                                  'automargin':True,      
                                  'gridcolor': 'black',
                                  'autorange': True,
                                  'showline': True},
                        'yaxis': {'range':[0,30],
                                  'title':'Gain, dB',
                                  'automargin':True,  
                                  'gridcolor': 'black',
                                  'autorange': True,
                                  'showline': True},
                        }
             }

default_bias_sweep_fig ={'data': [{'type': 'heatmap',
                                    'name': 'Trace 1',
                                    'x': [],
                                    'y': [],
                                    'z': [],
                                    'colorbar':{'orientation':'h',
                                                'thicknessmode':'fraction',
                                                'thickness':0.04,
                                                'xanchor':'center',
                                                'xref':'paper',
                                                'x':0.5,
                                                'xpad':10,
                                                'yanchor':'top',
                                                'yref':'container',
                                                'y':1,
                                                'ypad':15
                                                },
                                   'zmin': 0,
                                   'zmax': 1
                                  },
                                  {'type': 'scatter',
                                   'name': 'Trace 1',
                                   'x': [],
                                   'y': []}],
              'layout': {
                        'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
                        #'width': 350,
                        #'height':350,
                        #'plot_bgcolor': '#E5ECF6',
                        'xaxis': {#'range':[0,5],
                                  'title':'Current, mA',
                                  'automargin':True,      
                                  'gridcolor': 'black',
                                  'autorange': True,
                                  'showline': True},
                        'yaxis': {#'range':[-1,1],
                                  'title':'Frequency, GHz',
                                  'automargin':True,  
                                  'gridcolor': 'black',
                                  'autorange': True,
                                  'showline': True}
                        }
             }


@dataclass
class ChannelTab:
    """Channel tab UI content and related data"""
    tab:               ui.tab = None
    gain_plot:         ui.plotly = None
    gain_file:         hdf5_gain.HDF5GainFile = None
    gain_fig:          dict = field(default_factory=lambda: dict(default_gain_fig) )
    gain_file_toolbar_enabled:bool = False
    bias_sweep_file:   hdf5_bias_sweep.HDF5BiasSweepFile = None
    bias_sweep_plot:   ui.plotly = None
    bias_sweep_fig:    dict = field(default_factory=lambda: dict(default_bias_sweep_fig) )
    bias_sweep_file_toolbar_enabled:bool = False
    bias_sweep_cb_min: FloatUIParam = field(default_factory=lambda: FloatUIParam(
        name='Colorbar min',
        precision=None,
        unit=1,
        str_fmt='{:.3e}',
        min=None,
        max=None
    ))
    bias_sweep_cb_max: FloatUIParam = field(default_factory=lambda: FloatUIParam(
        name='Colorbar max',
        precision=None,
        unit=1,
        str_fmt='{:.3e}',
        min=None,
        max=None
    ))
    chan:              Channel = field(default_factory=lambda: Channel())
    log:               ui.log = None


@dataclass
class UiObjects:
    """Top level container for UI related data objects"""
    app_name: str = 'IMPA GUI'
    company_name: str = 'Bomj Systems'
    gain_plot_traces: GainPlotTraces = field(default_factory=lambda: GainPlotTraces())
    current_tab: str = None
    control_tab: ui.tab = None
    channel_tabs: list[ChannelTab] = field(default_factory=lambda: [])
    channel_name_id: dict[str, int] = field(default_factory=lambda: {})
    data_folder: str = "C:/"
