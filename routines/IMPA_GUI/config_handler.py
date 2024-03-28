import data_structures as ds
import yaml
from typing import Any
from jsonschema import validate
import json


def config_obj_from_dict(o: Any, d: dict) -> None:
    for key in d:
        if d[key] is dict:
            # Recursion
            config_obj_from_dict(getattr(o, key), d[key])
        else:
            attr = getattr(o, key)
            if ds.UIParameter in type(attr).mro():
                # If the parameter class is a child class of ds.UIParameter
                # than use appropriate methods to set it up
                attr.update(d[key])
            else:
                # If the parameter is a simple generic then just pass value
                setattr(o, key, d[key])


class ConfigHandler:
    def __init__(self, ui_objects: ds.UiObjects):
        self.ui_objects = ui_objects
        self.config_file_path = "config.yml"
        self.config_file_schema_path = "config_schema.json"
        self.bias_sweep_config_file_path = "bias_sweep_config.yml"
        self.bias_sweep_config_schema_path = "bias_sweep_config_schema.json"

    def load_config(self) -> None:
        f = open(self.config_file_path)
        f_sch = open(self.config_file_schema_path)
        config = yaml.load(f, yaml.CLoader)
        schema = json.load(f_sch)
        validate(config, schema)
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

    def load_bias_sweep_config(self) -> None:
        f = open(self.bias_sweep_config_file_path)
        config = yaml.load(f, yaml.CLoader)
        f_sch = open(self.bias_sweep_config_schema_path)
        schema = json.load(f_sch)
        validate(config, schema)
        for ch_data in config['channels']:
            ch_id = self.ui_objects.channel_name_id[ch_data['name']]
            bias_sweep = self.ui_objects.channel_tabs[ch_id].chan.bias_sweep
            config_obj_from_dict(bias_sweep, ch_data['parameters'])
        f.close()
        f_sch.close()


