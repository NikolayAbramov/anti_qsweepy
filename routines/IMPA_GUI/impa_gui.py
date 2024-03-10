from nicegui import ui
import numpy as np
import plotly.graph_objects as go
import time
from typing import Type
from data_structures import *
from file_picker.local_file_picker import local_file_picker
from hdf5_gain import HDF5GainFile
from hdf5_bias_sweep import HDF5BiasSweepFile
import traceback


async def pick_file() -> None:
    result = await local_file_picker('~', multiple=True)
    ui.notify(f'You chose {result}')


class UiDataProcessor:
    def __init__(self):
        tab1 = ChannelTab()
        tab1.chan.name = 'Channel 0'
        tab2 = ChannelTab()
        tab2.chan.name = 'Channel 1'
        self.ui_objects = UiObjects()
        self.ui_objects.channel_tabs = [tab1, tab2]

        #Queues
        self.q_command = None
        self.hardware_state = True
        
    def create_ui(self) -> None:
        @ui.refreshable
        def stop_run_label():
            if self.hardware_state:
                ui.label('Connected').classes('mt-2')
            else:
                ui.label('Disconnected').classes('mt-2')
                
        ui.page_title('IMPA')
        with ui.row(wrap=False).classes('w-full'):
            with ui.row(wrap=False).classes('w-72'):
                ui.label('Hardware:').classes('mt-2')
                ui.switch('').bind_value(self, 'hardware_state')\
                    .on('update:model-value',stop_run_label.refresh)
                stop_run_label()
            with ui.row(wrap=False).classes('w-full'):    
                ui.label('Karpovless IMPA tuning GUI')\
                    .classes('w-full text-xl text-center mt-2') 
        
        with ui.tabs() as tabs:
            control_tab = ui.tab("Control")
            for tab in self.ui_objects.channel_tabs:
                tab.tab = ui.tab(tab.chan.name)       
        with ui.tab_panels( tabs, value = self.ui_objects.channel_tabs[0].tab ).classes('w-full'):
            with ui.tab_panel(control_tab):
                ui.switch('VNA')
            for ch_id, tab in enumerate(self.ui_objects.channel_tabs):
                with ui.tab_panel(tab.tab):
                    self.fill_channel_tab(ch_id)
                    
    def fill_channel_tab( self, ch_id:int )->None:
        #ui.label(tab.chan.name)
        tab = self.ui_objects.channel_tabs[ch_id]
        pick_gain_file = lambda : self.pick_gain_file(ch_id)
        close_gain_file = lambda: self.close_gain_file(ch_id)
        brouse_gain_file_left = lambda: self.brouse_gain_file_left(ch_id)
        brouse_gain_file_right = lambda:self.brouse_gain_file_right(ch_id)
        
        pick_bias_sweep_file = lambda : self.pick_bias_sweep_file(ch_id)
        close_bias_sweep_file = lambda: self.close_bias_sweep_file(ch_id)
        
        with ui.row(wrap=False).classes('w-full'):
            #Gain plot
            with ui.column().classes('w-1/3'):
                tab.gain_plot = ui.plotly( tab.gain_fig ).classes('mr-2 w-full aspect-square')
                with ui.row().classes('w-full mt-1'):
                    ui.button('', on_click = pick_gain_file, icon='folder')\
                        .classes('text-xs mt-1 ml-1')\
                        .tooltip('Open file')
                    with ui.row(wrap = False).classes('space-x-1 ml-1 mt-1'):
                        ui.button('<', on_click = brouse_gain_file_left)\
                            .classes('text-xs')\
                            .bind_enabled( tab, 'gain_file_toolbar_enabled' )
                        ui.button('>', on_click = brouse_gain_file_right)\
                            .classes('text-xs')\
                            .bind_enabled( tab, 'gain_file_toolbar_enabled' )
                    ui.button('Set').classes('text-xs mt-1 ml-1').bind_enabled( tab, 'gain_file_toolbar_enabled' )
                    ui.button('Close', on_click = close_gain_file)\
                        .classes('text-xs mt-1 ml-1')\
                        .bind_enabled( tab, 'gain_file_toolbar_enabled' )
            #SvsBias plot    
            with ui.column().classes('w-1/3 h-full'):    
                tab.bias_sweep_plot = ui.plotly( tab.bias_sweep_fig ).classes('mr-2 w-full aspect-square')
                with ui.row().classes('w-full'):
                    ui.button('', on_click = pick_bias_sweep_file, icon='folder')\
                        .classes('text-xs mt-2 ml-1')\
                        .tooltip('Open file')
                    ui.button('Update', on_click = tab.bias_sweep_plot.update )\
                        .classes('text-xs mt-2 ml-1')\
                        .bind_enabled( tab, 'bias_sweep_file_toolbar_enabled' )\
                        .tooltip('Yes, you have to because this shit is slow :(')
                    ui.button('Close', on_click = close_bias_sweep_file )\
                        .classes('text-xs mt-2 ml-1')\
                        .bind_enabled( tab, 'bias_sweep_file_toolbar_enabled' )
            #Controls            
            with ui.column(wrap=False).classes('w-1/3'):
                with ui.tabs().props('no-caps dense').classes('text-xs') as tabs:
                    control_tab = ui.tab("Control")
                    vna_tab = ui.tab("VNA")
                    optimization_tab = ui.tab("Optimization")
                    sweep_tab = ui.tab("Bias sweep")
                with ui.tab_panels( tabs, value = control_tab ).classes('w-full'):
                    with ui.tab_panel(control_tab):    
                        self.fill_control_tab(ch_id)
                    with ui.tab_panel(vna_tab):    
                        self.fill_vna_tab(ch_id)
                    with ui.tab_panel(optimization_tab):    
                        self.fill_optimization_tab(ch_id)
                    with ui.tab_panel(sweep_tab):    
                        self.fill_bias_sweep_tab(ch_id)    
        # Log
        tab.log = ui.log(max_lines=100).classes('w-full h-30')
    
    def fill_control_tab(self, ch_id: int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        with ui.row(wrap=False):
            ui.switch('Pump')
            ui.switch('Bias')
        self.create_inp_w_step_and_btns(ch_id, tab.chan.pump_frequency)
        self.create_inp_w_step_and_btns(ch_id, tab.chan.pump_power)
        self.create_inp_w_step_and_btns(ch_id, tab.chan.bias_current)
        with ui.row(wrap=False):
            ui.select({0:'Bias sweep',1:'Optimization', 2:'Normalize' }, value = 2)\
                .classes('text-xs')
            ui.button('Run').classes('text-xs mt-4 ml-1')
            ui.button('Abort').classes('text-xs mt-4 ml-1')
            
    def fill_vna_tab(self, ch_id: int) -> None:
        pass
        
    def fill_optimization_tab(self, ch_id: int) -> None:
        pass
    
    def fill_bias_sweep_tab(self, ch_id: int) -> None:
        pass
                    
    def validate_float(self, s: str) -> str|None:
        if s == "":
            return None
        try:
            float(s)
        except ValueError:
            return "Not a float!"
        return None
    
    def create_inp_w_step_and_btns(self, ch_id: int, p: FloatUIParam ) -> None:
        change_float = lambda: self.change_float_param(ch_id, p)
        inc_float = lambda: self.inc_param(ch_id, p)
        dec_float = lambda: self.dec_param(ch_id, p)
        with ui.row(wrap=False):
            inp = ui.input(label = p.name, validation = self.validate_float).bind_value( p, 'str_repr')
            inp.on('keydown.enter', change_float )
            inp.bind_enabled(p, 'enabled')
            inp.classes('w-36')
            ui.button('+').bind_enabled(p, 'enabled')\
                .on('click', inc_float, throttle = 0.2 )\
                .classes('text-xs ml-0 mr-1 mb-0 mt-3')
            ui.button('-').bind_enabled(p, 'enabled')\
                .on('click', dec_float, throttle = 0.2 )\
                .classes('text-xs ml-0 mr-1 mb-0 mt-3')
            ui.select( p.step_sel , value = 0.1, label = "Step" ).bind_value( p, 'step')

    def change_float_param(self, ch_id: int, p: FloatUIParam) -> None:
        val = float(p.str_repr)
        p.value = round(val/p.precision)*p.precision
        p.str_repr = p.str_fmt.format(p.value)
        self.queue_param(ch_id, p)
        
    def inc_param(self, ch_id: int, p: FloatUIParam) -> None:
        p.value += p.step
        self.queue_param(ch_id, p)
        
    def dec_param(self, ch_id: int, p: FloatUIParam) -> None:
        p.value -= p.step
        self.queue_param(ch_id, p)

    def queue_param(self, ch_id, p: FloatUIParam) -> None:
        p.enabled = False
        if self.q_command.empty():
            self.q_command.put({'op': p.method, 'args': (p.value, ch_id)})
                
    async def pick_gain_file(self, ch_id:int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        result = await local_file_picker('~', multiple=False)
        if result is not None:
            result = result[0]
            try:
                tab.gain_file = HDF5GainFile( result, mode = 'r' )
            except Exception as err:
                tab.log.push("Unable to open file:"+result)
                traceback.print_exc()
            else:
                tab.log.push("Opened gain file:"+result)
                tab.gain_file_toolbar_enabled = True
                if not self.update_gain_plot_from_file(ch_id):
                    self.close_gain_file( ch_id )
                    
    def update_gain_plot_from_file(self, ch_id: int) -> bool:
        tab = self.ui_objects.channel_tabs[ch_id]
        data = tab.gain_file.get_data()
        if data['status']:
            tab.gain_fig['data'] = [dict(default_gain_fig_data),dict(default_gain_fig_data)]
            tab.gain_fig['data'][0]['x'] = data['frequency']
            tab.gain_fig['data'][0]['y'] = data['gain']
            tab.gain_fig['data'][0]['name'] = 'Gain'
            tab.gain_fig['data'][1]['x'] = data['frequency']
            tab.gain_fig['data'][1]['y'] = data['snr_gain']
            tab.gain_fig['data'][1]['name'] = 'SNR gain'
            tab.gain_fig['layout']['annotations'][0]['text'] = data['info']
            tab.gain_plot.update()
            tab.bias_sweep_fig['data'][1]['x'] = [data['Ib'],] 
            tab.bias_sweep_fig['data'][1]['y'] = [data['Fs'],]
            #tab.bias_sweep_plot.update()
            return True
        else:
            tab.log.push(data['message'])
            return False
                
    def brouse_gain_file_left(self, ch_id: int):
        tab = self.ui_objects.channel_tabs[ch_id]
        if tab.gain_file.backward():
            self.update_gain_plot_from_file(ch_id)
    
    def brouse_gain_file_right(self,ch_id: int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        if tab.gain_file.forward():
            self.update_gain_plot_from_file(ch_id)
    
    def close_gain_file(self, ch_id: int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        tab.log.push("Gain file closed:"+tab.gain_file.filename)
        tab.gain_file.close()
        del tab.gain_file
        tab.gain_file_toolbar_enabled = False
        
    async def pick_bias_sweep_file( self, ch_id: int) -> None:
        tab = self.ui_objects.channel_tabs[ch_id]
        result = await local_file_picker('~', multiple=False)
        if result is not None:
            result = result[0]
            try:
                tab.bias_sweep_file = HDF5BiasSweepFile(result, mode='r')
            except Exception as err:
                tab.log.push( "Unable to open file:"+result)
                traceback.print_exc()
            else:
                tab.log.push( "Opened bias sweep file:"+result)
                tab.bias_sweep_file_toolbar_enabled = True
                if not self.update_bias_sweep_plot_from_file(ch_id):
                    self.close_bias_sweep_file(ch_id)
                
    def update_bias_sweep_plot_from_file(self, ch_id: int) -> bool:
        tab = self.ui_objects.channel_tabs[ch_id]
        data = tab.bias_sweep_file.get_data()
        if data['status']:
            tab.bias_sweep_fig['data'][0]['x'] = data['current']
            tab.bias_sweep_fig['data'][0]['y'] = data['frequency']
            tab.bias_sweep_fig['data'][0]['z'] = data['delay'].tolist()
            tab.bias_sweep_plot.update()
            return True
        else:
            tab.log.push( data['message'] )
            return False
                
    def close_bias_sweep_file(self, ch_id:int)->None:
        tab = self.ui_objects.channel_tabs[ch_id]
        tab.log.push("Bias sweep file closed:"+tab.bias_sweep_file.filename)
        tab.bias_sweep_file.close()
        del tab.bias_sweep_file
        tab.bias_sweep_file_toolbar_enabled = False
        tab.bias_sweep_fig['data'][0]['x'] = []
        tab.bias_sweep_fig['data'][0]['y'] = []
        tab.bias_sweep_fig['data'][0]['z'] = []
        tab.bias_sweep_plot.update()

    def request_vna_data(self):
        self.q_command.put({'op': 'get_vna_data', 'args': (0,)})
