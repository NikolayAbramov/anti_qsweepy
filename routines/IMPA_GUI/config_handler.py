import data_structures as ds
import yaml
from typing import Any


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

    def load_config(self) -> None:
        f = open(self.config_file_path)
        config = yaml.load(f, yaml.CLoader)
        for ch_id in range(len(config['channels'])):
            ch_config = config['channels'][ch_id]
            tab = ds.ChannelTab()
            tab.chan.name = ch_config['name']
            config_obj_from_dict(tab.chan.vna, ch_config['vna'])
            config_obj_from_dict(tab.chan.bias_source, ch_config['bias_source'])
            config_obj_from_dict(tab.chan.pump_source, ch_config['pump_source'])
            self.ui_objects.channel_tabs += [tab]
            self.ui_objects.channel_name_id.update({ch_config['name']:ch_id})
