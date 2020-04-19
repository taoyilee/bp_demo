#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import os
from pathlib import Path

from appdirs import user_config_dir
from configobj import ConfigObj

import uci_cbp_demo
from uci_cbp_demo.logging import logger


class Descriptor:
    data = None

    def __init__(self, default):
        self.default = default

        self.parent = None

    def __get__(self, instance, owner):
        return self.data

    def __set__(self, instance, value):
        logger.info(f"value updated: {value}")
        self.data = value
        if instance.parent is not None:
            logger.info(f"parent written")
            instance.parent.write()


class BooleanAsIntDescriptor(Descriptor):
    data = False

    def __get__(self, instance, owner):
        return int(self.data)


class Section:
    @property
    def attributes(self):
        return set(self.__class__.__dict__.keys()) - {'__doc__', '__module__'}

    def to_dict(self):
        return {k: getattr(self, k) for k in self.attributes if getattr(self, k) is not None}

    def __init__(self, parent: "Configuration"):
        assert isinstance(parent, Configuration)
        self.parent = parent
        for k in self.attributes:
            getattr(self, k + "_descriptor").parent = self.parent

    def __getattribute__(self, key):
        if "_descriptor" in key:
            return self.__class__.__dict__[key.replace("_descriptor", "")]
        v = object.__getattribute__(self, key)
        if hasattr(v, '__get__'):
            return v.__get__(None, self)
        return v

    def update(self, newdata):
        for key, value in newdata.items():
            if key != "parent":
                logger.info(f"{key} -> {value}")
                setattr(self, key, value)


class PlottingSection(Section):
    imu_en = BooleanAsIntDescriptor(True)
    ch1_en = BooleanAsIntDescriptor(True)
    ch2_en = BooleanAsIntDescriptor(True)
    autoscale_cap = BooleanAsIntDescriptor(True)


class BoardSection(Section):
    mac = Descriptor("DC:4E:6D:9F:E3:BA")
    dac_a = Descriptor(0)
    dac_b = Descriptor(0)


class Configuration:
    DEFAULT_CONFIG = Path(os.path.dirname(os.path.realpath(__file__))) / "config.ini"

    def __init__(self, config: "ConfigObj"):
        self._config = config
        logger.info(f"Init with: {config}")
        self.plotting = PlottingSection(self)
        self.board = BoardSection(self)
        self.plotting.update(config["plotting"])
        self.board.update(config["board"])
        self.write()

    @classmethod
    def from_file(cls, filename):
        loaded = ConfigObj(filename)
        logger.info(f"Loaded configuration from {filename}")
        new_instance = cls(loaded)
        return new_instance

    @classmethod
    def default(cls, filename):
        logger.info(f"Loaded DEFAULT configuration from {str(cls.DEFAULT_CONFIG)}")
        loaded = ConfigObj(str(cls.DEFAULT_CONFIG))
        loaded.filename = filename
        new_instance = cls(loaded)
        return new_instance

    def write(self):
        if str(self._config.filename) == str(self.DEFAULT_CONFIG):
            raise ValueError(f"Cannot write into default configuration file")
        logger.info(f"Saving configuration to {self._config.filename}")
        self._config["plotting"].update(self.plotting.to_dict())
        self._config["board"].update(self.board.to_dict())
        self._config.write()


config_dir = Path(user_config_dir(uci_cbp_demo.__appname__, uci_cbp_demo.__author__))
config_dir.mkdir(exist_ok=True)
config_file = config_dir / "config.ini"

if config_file.is_file():
    config = Configuration.from_file(str(config_file))
else:
    config = Configuration.default(config_file)
    config.write()