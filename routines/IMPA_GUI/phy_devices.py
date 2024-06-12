import anti_qsweepy.drivers as drv

from dataclasses import dataclass
from typing import Any


@dataclass
class PhyDevice:
    """Physical device class

    Attributes:
        driver_name (str): Device driver name within the anti_qsweepy.drivers module
        class_name (str): Device class name within the driver
        chan (int): Associated physical device channel
        dev_inst: Device class instance
        similar_ui_ch (list): List of UI channels sharing the same device with the
                              same driver_name and associated physical channel"""
    driver_name: str
    class_name: str
    chan: int
    dev_inst: Any
    similar_ui_ch: list[int]


@dataclass
class BiasSource(PhyDevice):
    dev_inst: drv.Dummy_CurrentSource.CurrentSource


@dataclass
class PumpSource(PhyDevice):
    dev_inst: drv.Dummy_Generator.Generator


@dataclass
class VNA(PhyDevice):
    dev_inst: drv.Dummy_VNA.NetworkAnalyzer