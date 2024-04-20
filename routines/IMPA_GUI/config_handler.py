import data_structures as ds
#import yaml
import ruamel.yaml as yaml
from typing import Any
from jsonschema import validate
import json
import platformdirs
import shutil
from dataclasses import dataclass
from pathlib import Path
import copy


def config_obj_from_dict(o: Any, d: dict) -> None:
    for key in d:
        if type(d[key]) is dict:
            # Recursion
            config_obj_from_dict(getattr(o, key), d[key])
        else:
            attr = getattr(o, key)
            if type(attr) is ds.FloatListUIParameter:
                attr.str_repr = d[key]
            elif ds.UIParameter in type(attr).mro():
                # If the parameter class is a child class of ds.UIParameter
                # than use appropriate methods to set it up
                attr.update(d[key])
            else:
                # If the parameter is a simple generic then just pass value
                setattr(o, key, d[key])


def fill_map_from_object(o: Any, d: yaml.CommentedMap) -> None:
    for key in d:
        if type(d[key]) is yaml.CommentedMap:
            # Recursion
            fill_map_from_object(getattr(o, key), d[key])
        else:
            attr = getattr(o, key)
            if type(attr) is ds.FloatListUIParameter:
                d[key] = attr.str_repr
            elif ds.UIParameter in type(attr).mro():
                d[key] = attr.get_value()
            else:
                # If the parameter is a simple generic then just pass value
                d[key] = attr


@dataclass
class DefaultConfigFiles:
    path: Path = Path("default_configs")
    config: Path = path/"config.yml"
    config_schema: Path = path/"config_schema.json"
    bias_sweep: Path = path/"bias_sweep_config.yml"
    bias_sweep_schema: Path = path/"bias_sweep_config_schema.json"
    optimization: Path = path/'optimization_config.yml'
    optimization_schema: Path = path/'optimization_config_schema.json'


@dataclass
class UserConfigFiles:
    path: Path
    config: Path
    bias_sweep: Path
    optimization: Path


class ConfigHandler:
    def __init__(self, ui_objects: ds.UiObjects):
        self.ui_objects = ui_objects
        self.default_config_files = DefaultConfigFiles()
        app_name = self.ui_objects.app_name.replace(' ', '_')
        platformdirs.user_data_path()
        base_pth = platformdirs.user_documents_path()
        pth = base_pth/app_name
        self.user_config_files = UserConfigFiles(path=pth,
                                                 config=pth/self.default_config_files.config.parts[-1],
                                                 bias_sweep=pth/self.default_config_files.bias_sweep.parts[-1],
                                                 optimization=pth/self.default_config_files.optimization.parts[-1])
        if not pth.exists():
            pth.mkdir()
            self._create_initial_config(pth)
            shutil.copy(self.default_config_files.bias_sweep, pth)
            shutil.copy(self.default_config_files.optimization, pth)
            return

        if not self.user_config_files.config.exists():
            self._create_initial_config(pth)

        if not self.user_config_files.bias_sweep.exists():
            shutil.copy(self.default_config_files.bias_sweep, pth)

        if not self.user_config_files.optimization.exists():
            shutil.copy(self.default_config_files.optimization, pth)

    def _create_initial_config(self, pth: Path) -> None:
        shutil.copy(self.default_config_files.config, pth)
        yaml_inst = yaml.YAML()
        config = yaml_inst.load(self.user_config_files.config)
        base_pth = platformdirs.user_documents_path()
        config['data_dir'] = str(base_pth / 'IMPA_data')
        yaml_inst.dump(config, self.user_config_files.config)

    def load_config(self) -> None:
        f = open(self.user_config_files.config)
        f_sch = open(self.default_config_files.config_schema)
        config = yaml.load(f, yaml.Loader)#, yaml.CLoader)
        schema = json.load(f_sch)
        validate(config, schema)
        self.ui_objects.data_folder = config['data_dir']
        self.ui_objects.tcp_ip_port = config['tcp_ip_port']
        for ch_id in range(len(config['channels'])):
            ch_config = config['channels'][ch_id]
            tab = ds.ChannelTab()
            tab.chan.name = ch_config['name']
            config_obj_from_dict(tab.chan.vna, ch_config['vna'])
            config_obj_from_dict(tab.chan.bias_source, ch_config['bias_source'])
            config_obj_from_dict(tab.chan.pump_source, ch_config['pump_source'])
            self.ui_objects.channel_tabs += [tab]
            self.ui_objects.channel_name_id.update({ch_config['name']:ch_id})
        f.close()
        f_sch.close()
        self.load_bias_sweep_config()
        self.load_optimization_config()

    def load_bias_sweep_config(self) -> None:
        f = open(self.user_config_files.bias_sweep)
        config = yaml.load(f, yaml.Loader)#, yaml.CLoader)
        f_sch = open(self.default_config_files.bias_sweep_schema)
        schema = json.load(f_sch)
        validate(config, schema)
        for ch_data in config['channels']:
            try:
                ch_id = self.ui_objects.channel_name_id[ch_data['name']]
            except KeyError:
                continue
            bias_sweep = self.ui_objects.channel_tabs[ch_id].chan.bias_sweep
            config_obj_from_dict(bias_sweep, ch_data['parameters'])
        f.close()
        f_sch.close()

    def load_optimization_config(self) -> None:
        f = open(self.user_config_files.optimization)
        config = yaml.load(f, yaml.Loader)#, yaml.CLoader)
        f_sch = open(self.default_config_files.optimization_schema)
        schema = json.load(f_sch)
        validate(config, schema)
        for ch_data in config['channels']:
            try:
                ch_id = self.ui_objects.channel_name_id[ch_data['name']]
            except KeyError:
                continue
            obj = self.ui_objects.channel_tabs[ch_id].chan.optimization
            config_obj_from_dict(obj, ch_data['parameters'])
        f.close()
        f_sch.close()

    def save_config(self) -> None:
        yaml_inst = yaml.YAML()
        config = yaml_inst.load(self.default_config_files.config)
        bias_sweep_config = yaml_inst.load(self.default_config_files.bias_sweep)
        optimization_config = yaml_inst.load(self.default_config_files.optimization)
        n_ch = len(self.ui_objects.channel_tabs)
        config['data_dir'] = self.ui_objects.data_folder
        config['tcp_ip_port'] = self.ui_objects.tcp_ip_port
        for ch_id in range(n_ch):
            if ch_id:
                config['channels'].append(copy.deepcopy(config['channels'][0]))
                bias_sweep_config['channels'].append(copy.deepcopy(bias_sweep_config['channels'][0]))
                optimization_config['channels'].append(copy.deepcopy(optimization_config['channels'][0]))
            chan = self.ui_objects.channel_tabs[ch_id].chan
            fill_map_from_object(chan, config['channels'][ch_id])
            bias_sweep = self.ui_objects.channel_tabs[ch_id].chan.bias_sweep
            bias_sweep_config['channels'][ch_id]['name'] = chan.name
            fill_map_from_object(bias_sweep, bias_sweep_config['channels'][ch_id]['parameters'])
            optimization = self.ui_objects.channel_tabs[ch_id].chan.optimization
            fill_map_from_object(optimization, optimization_config['channels'][ch_id]['parameters'])
        yaml_inst.dump(config, self.user_config_files.config)
        yaml_inst.dump(bias_sweep_config, self.user_config_files.bias_sweep)
        yaml_inst.dump(optimization_config, self.user_config_files.optimization)
