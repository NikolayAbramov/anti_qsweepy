from nicegui import ui
from typing import Callable
import data_structures as ds
import ui_callbacks as ui_cb


def validate_float(s: str) -> str | None:
    """Float validator for string input"""
    if s in ['', '+', '-']:
        return None
    try:
        float(s)
    except ValueError:
        #return "Not a float!"
        return ''
    return None


class UiGenerator:
    def __init__(self, ui_objects: ds.UiObjects, cb: ui_cb.UiCallbacks):
        self.ui_objects = ui_objects
        self.cb = cb
        self.hardware_state = True

    def create_ui(self) -> None:
        @ui.refreshable
        def stop_run_label():
            if self.hardware_state:
                ui.label('Connected').classes('mt-2')
            else:
                ui.label('Disconnected').classes('mt-2')

        ui.add_head_html('''
            <style>
                :root {
                    --nicegui-default-padding: 0rem;
                    --nicegui-default-gap: 0rem;
                }
            </style>
        ''')
        ui.button.default_classes('text-xs')

        ui.page_title('IMPA')
        with ui.row(wrap=False).classes('w-full'):
            with ui.row(wrap=False).classes('w-72'):
                ui.label('Hardware:').classes('mt-2')
                ui.switch('').bind_value(self, 'hardware_state') \
                    .on('update:model-value', stop_run_label.refresh)
                stop_run_label()
            with ui.row(wrap=False).classes('w-full'):
                ui.label('Karpovless IMPA tuning GUI') \
                    .classes('w-full text-xl text-center mt-2')

        with ui.tabs() as tabs:
            control_tab = ui.tab("Control")
            for tab in self.ui_objects.channel_tabs:
                tab.tab = ui.tab(tab.chan.name)
        with ui.tab_panels(tabs, value=self.ui_objects.channel_tabs[0].tab).classes('w-full'):
            with ui.tab_panel(control_tab):
                ui.switch('VNA')
            for ch_id, tab in enumerate(self.ui_objects.channel_tabs):
                with ui.tab_panel(tab.tab):
                    self._fill_channel_tab(ch_id)

    def _fill_channel_tab(self, ch_id: int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        pick_gain_file = lambda: self.cb.pick_gain_file(ch_id)
        close_gain_file = lambda: self.cb.close_gain_file(ch_id)
        browse_gain_file_left = lambda: self.cb.browse_gain_file_left(ch_id)
        browse_gain_file_right = lambda: self.cb.browse_gain_file_right(ch_id)
        pick_bias_sweep_file = lambda: self.cb.pick_bias_sweep_file(ch_id)
        update_bias_sweep_plot_from_file = lambda: self.cb.update_bias_sweep_plot_from_file(ch_id)
        close_bias_sweep_file = lambda: self.cb.close_bias_sweep_file(ch_id)

        with ui.row(wrap=False).classes('w-full'):
            # Gain plot
            with ui.column().classes('w-1/3'):
                tab.gain_plot = ui.plotly(tab.gain_fig).classes('mr-2 w-full aspect-square')
                with ui.row().classes('w-full mt-1'):
                    ui.button('', on_click=pick_gain_file, icon='folder') \
                        .classes('text-xs mt-1 ml-1') \
                        .tooltip('Open file')
                    with ui.row(wrap=False).classes('space-x-1 ml-1 mt-1'):
                        ui.button('<', on_click=browse_gain_file_left) \
                            .classes('text-xs') \
                            .bind_enabled(tab, 'gain_file_toolbar_enabled')
                        ui.button('>', on_click=browse_gain_file_right) \
                            .classes('text-xs') \
                            .bind_enabled(tab, 'gain_file_toolbar_enabled')
                    ui.button('Set').classes('text-xs mt-1 ml-1').bind_enabled(tab, 'gain_file_toolbar_enabled')
                    ui.button('Close', on_click=close_gain_file) \
                        .classes('text-xs mt-1 ml-1') \
                        .bind_enabled(tab, 'gain_file_toolbar_enabled')
            # SvsBias plot
            with ui.column().classes('w-1/3 h-full'):
                tab.bias_sweep_plot = ui.plotly(tab.bias_sweep_fig).classes('mr-2 w-full aspect-square')
                with ui.row().classes('w-full'):
                    ui.button('', on_click=pick_bias_sweep_file, icon='folder') \
                        .classes('text-xs mt-2 ml-1') \
                        .tooltip('Open file')
                    ui.button('Update', on_click=update_bias_sweep_plot_from_file) \
                        .classes('text-xs mt-2 ml-1') \
                        .bind_enabled(tab, 'bias_sweep_file_toolbar_enabled') \
                        .tooltip('Yes, you have to because this shit is slow :(')
                    ui.button('Close', on_click=close_bias_sweep_file) \
                        .classes('text-xs mt-2 ml-1') \
                        .bind_enabled(tab, 'bias_sweep_file_toolbar_enabled')
            # Controls
            with ui.column(wrap=False).classes('w-1/3'):
                with ui.tabs().props('no-caps dense').classes('text-xs') as tabs:
                    control_tab = ui.tab("Control")
                    vna_tab = ui.tab("VNA")
                    optimization_tab = ui.tab("Optimization")
                    sweep_tab = ui.tab("Bias sweep")
                with ui.tab_panels(tabs, value=control_tab).classes('w-full'):
                    with ui.tab_panel(control_tab):
                        self._fill_control_tab(ch_id)
                    with ui.tab_panel(vna_tab):
                        self._fill_vna_tab(ch_id)
                    with ui.tab_panel(optimization_tab):
                        self._fill_optimization_tab(ch_id)
                    with ui.tab_panel(sweep_tab):
                        self._fill_bias_sweep_tab(ch_id)
        # Log
        tab.log = ui.log(max_lines=100).classes('w-full h-30')

    def _fill_control_tab(self, ch_id: int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]

        def toggle_pump_output_cb():
            self.cb.toggle_bool_param(ch_id,
                                      self.ui_objects.channel_tabs[ch_id].chan.pump_source.output)

        def toggle_bias_output_cb():
            self.cb.toggle_bool_param(ch_id,
                                      self.ui_objects.channel_tabs[ch_id].chan.bias_source.output)
        with ui.row(wrap=False):
            ui.switch('Pump')\
                .bind_value_from(self.ui_objects.channel_tabs[ch_id].chan.pump_source.output, 'value')\
                .bind_enabled(self.ui_objects.channel_tabs[ch_id].chan.pump_source.output, 'enabled')\
                .on('click', toggle_pump_output_cb)
            ui.switch('Bias') \
                .bind_value_from(self.ui_objects.channel_tabs[ch_id].chan.bias_source.output, 'value')\
                .bind_enabled(self.ui_objects.channel_tabs[ch_id].chan.bias_source.output, 'enabled')\
                .on('click', toggle_bias_output_cb)
        self._create_inp_w_step_and_btns(ch_id, tab.chan.pump_source.frequency,
                                         callback=self.cb.set_pump_freq,
                                         inc_callback=self.cb.inc_pump_freq,
                                         dec_callback=self.cb.dec_pump_freq)
        self._create_inp_w_step_and_btns(ch_id, tab.chan.pump_source.power)
        self._create_inp_w_step_and_btns(ch_id, tab.chan.bias_source.current)
        with ui.row(wrap=False):
            ui.select({0: 'Bias sweep', 1: 'Optimization', 2: 'Normalize'}, value=2) \
                .classes('text-xs')
            ui.button('Run').classes('text-xs mt-4 ml-1')
            ui.button('Abort').classes('text-xs mt-4 ml-1')

    def _fill_vna_tab(self, ch_id: int) -> None:
        ch_tab = self.ui_objects.channel_tabs[ch_id]
        # Callbacks
        connect_btn_cb = lambda: self.cb.toggle_vna_connection(ch_id)
        bandwidth_cb = lambda: self.cb.change_float_param(ch_id, ch_tab.chan.vna.bandwidth)
        span_cb = lambda: self.cb.change_float_param(ch_id, ch_tab.chan.vna.span)
        center_cb = lambda: self.cb.change_float_param(ch_id, ch_tab.chan.vna.center)
        pump_center_bind_cb = lambda: self.cb.bind_pump_freq_to_vna_center(ch_id)
        points_cb = lambda: self.cb.change_float_param(ch_id, ch_tab.chan.vna.points)
        power_cb = lambda: self.cb.change_float_param(ch_id, ch_tab.chan.vna.power)
        with ui.column():
            # Connect/disconnect button
            ui.button('Connect', on_click=connect_btn_cb) \
                .bind_enabled(ch_tab.chan.vna.is_connected, 'enabled') \
                .bind_text(ch_tab.chan.vna.is_connected, 'str_repr') \
                .classes('w-28')
            # Bandwidth input
            with ui.row(wrap=False):
                ui.input(label='Bandwidth', validation=validate_float) \
                    .on('keydown.enter', bandwidth_cb)\
                    .bind_value(ch_tab.chan.vna.bandwidth, 'str_repr')\
                    .bind_enabled(ch_tab.chan.vna.bandwidth, 'enabled')\
                    .classes('w-20')
                ui.label("Hz").classes('mt-6')
            # Center input
            with ui.row(wrap=False):
                ui.input(label='Center', validation=validate_float) \
                    .on('keydown.enter', center_cb)\
                    .bind_value(ch_tab.chan.vna.center, 'str_repr')\
                    .bind_enabled(ch_tab.chan.vna.center, 'enabled')\
                    .classes('w-20')
                ui.label("GHz").classes('mt-6')
                ui.switch('Bind pump', on_change=pump_center_bind_cb) \
                    .bind_value(ch_tab.chan.vna.pump_center_bind, 'value')\
                    .bind_enabled(ch_tab.chan.vna.pump_center_bind, 'enabled')\
                    .classes('mt-2')
            # Span input
            with ui.row(wrap=False):
                ui.input(label='Span', validation=validate_float) \
                    .on('keydown.enter', span_cb)\
                    .bind_value(ch_tab.chan.vna.span, 'str_repr')\
                    .bind_enabled(ch_tab.chan.vna.span, 'enabled')\
                    .classes('w-20')
                ui.label("GHz").classes('mt-6')
            # Number of points input
            with ui.row(wrap=False):
                ui.input(label='Sweep points', validation=validate_float) \
                    .on('keydown.enter', points_cb) \
                    .bind_value(ch_tab.chan.vna.points, 'str_repr') \
                    .bind_enabled(ch_tab.chan.vna.points, 'enabled') \
                    .classes('w-20')
            # Power input
            with ui.row(wrap=False):
                ui.input(label='Power', validation=validate_float) \
                    .on('keydown.enter', power_cb) \
                    .bind_value(ch_tab.chan.vna.power, 'str_repr') \
                    .bind_enabled(ch_tab.chan.vna.power, 'enabled') \
                    .classes('w-20')
                ui.label("dBm").classes('mt-6')

    def _fill_optimization_tab(self, ch_id: int) -> None:
        pass

    def _fill_bias_sweep_tab(self, ch_id: int) -> None:
        chan = self.ui_objects.channel_tabs[ch_id].chan
        start_btn_cb = lambda: self.cb.start_stop_bias_sweep(ch_id)
        with ui.column():
            with ui.row(wrap=False):
                # Run/abort button
                ui.button('Start', on_click=start_btn_cb) \
                    .bind_enabled(chan.bias_sweep.is_running, 'enabled') \
                    .bind_text(chan.bias_sweep.is_running, 'str_repr') \
                    .classes('w-28')
                ui.circular_progress(min = 0, max = 100)\
                    .bind_value_from(chan.bias_sweep, 'progress')\
                    .bind_visibility_from(chan.bias_sweep.is_running, 'value')\
                    .classes('ml-4')
            # Start input
            with ui.row(wrap=False):
                with ui.column():
                    self._create_parameter_input(chan.bias_sweep.bias_start, 'w-28')
                    self._create_parameter_input(chan.bias_sweep.bias_stop, 'w-28')
                    self._create_parameter_input(chan.bias_sweep.bias_step, 'w-28')
                    self._create_parameter_input(chan.bias_sweep.vna_bandwidth, 'w-28')
                with ui.column().classes('ml-4'):
                    self._create_parameter_input(chan.bias_sweep.vna_start, 'w-28')
                    self._create_parameter_input(chan.bias_sweep.vna_stop, 'w-28')
                    self._create_parameter_input(chan.bias_sweep.vna_points, 'w-28')
                    self._create_parameter_input(chan.bias_sweep.vna_power, 'w-28')

    def _create_parameter_input(self, p: ds.UIParameter, classes: str = 'w-20') -> None:
        ui.input(label=p.name, validation=validate_float)\
            .on('keydown.enter', p.update_val)\
            .on('blur',  p.update_val)\
            .bind_value(p, 'str_repr')\
            .bind_enabled(p, 'enabled')\
            .classes(classes)

    def _create_inp_w_step_and_btns(self,
                                    ch_id: int,
                                    p: ds.FloatUIParam,
                                    callback: Callable= None,
                                    inc_callback: Callable = None,
                                    dec_callback: Callable = None) -> None:
        """Creates special input with +- buttons for main parameters:
        pump_frequency, pump_power, bias_current"""
        if callback is None:
            change_float = lambda: self.cb.change_float_param(ch_id, p)
        else:
            change_float = lambda: callback(ch_id, p)

        if inc_callback is None:
            inc_float = lambda: self.cb.inc_param(ch_id, p)
        else:
            inc_float = lambda: inc_callback(ch_id, p)

        if dec_callback is None:
            dec_float = lambda: self.cb.dec_param(ch_id, p)
        else:
            dec_float = lambda: dec_callback(ch_id, p)

        with ui.row(wrap=False):
            inp = ui.input(label=p.name, validation=validate_float).bind_value(p, 'str_repr')
            inp.on('keydown.enter', change_float)
            inp.bind_enabled(p, 'enabled')
            inp.classes('w-36')
            ui.button('+').bind_enabled(p, 'enabled') \
                .on('click', inc_float, throttle=0.2) \
                .classes('text-xs ml-0 mr-1 mb-0 mt-3')
            ui.button('-').bind_enabled(p, 'enabled') \
                .on('click', dec_float, throttle=0.2) \
                .classes('text-xs ml-0 mr-1 mb-0 mt-3')
            ui.select(p.step_sel, value=0.1, label="Step").bind_value(p, 'step')
