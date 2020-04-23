#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
import os
from pathlib import Path

from appdirs import user_config_dir, user_log_dir, user_data_dir
from configobj import ConfigObj

import uci_cbp_demo
from uci_cbp_demo.logging import logger


class Descriptor:
    data = None

    def __init__(self, default):
        self.write = False
        self.data = default
        self.parent = None

    def __get__(self, instance, owner):
        return self.data

    def __set__(self, instance, value):
        self.data = value
        if self.write and instance.parent is not None:
            instance.parent.write()


class BooleanAsIntDescriptor(Descriptor):
    data = False

    def __get__(self, instance, owner):
        return int(self.data)


class StringDescriptor(Descriptor):
    data = False

    def __get__(self, instance, owner):
        return str(self.data)


class Section:
    @property
    def attributes(self):
        return set(self.__class__.__dict__.keys()) - {'__doc__', '__module__', 'name'}

    def to_dict(self):
        aa = {k: getattr(self, k) for k in self.attributes}
        logger.info(f"{self.name} {self.attributes} {aa}")
        return {k: getattr(self, k) for k in self.attributes if getattr(self, k) is not None}

    def __init__(self, parent: "Configuration"):
        assert isinstance(parent, Configuration)
        self.parent = parent
        for k in self.attributes:
            getattr(self, k + "_descriptor").parent = self.parent

    def enable_autowrite(self):
        for k in self.attributes:
            getattr(self, k + "_descriptor").write = True

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
                setattr(self, key, value)


class PlottingSection(Section):
    name = "plotting"
    imu_en = BooleanAsIntDescriptor(True)
    ch1_en = BooleanAsIntDescriptor(True)
    ch2_en = BooleanAsIntDescriptor(True)
    autoscale_cap = BooleanAsIntDescriptor(True)


class BoardSection(Section):
    name = "board"
    mac = StringDescriptor("DC:4E:6D:9F:E3:BA")
    dac1 = Descriptor(0)
    dac2 = Descriptor(0)


class DefaultSection(Section):
    name = "DEFAULT"
    log_dir = StringDescriptor(user_log_dir(uci_cbp_demo.__appname__, uci_cbp_demo.__author__))
    data_dir = StringDescriptor(user_data_dir(uci_cbp_demo.__appname__, uci_cbp_demo.__author__))


class Configuration:
    DEFAULT_CONFIG = Path(os.path.dirname(os.path.realpath(__file__))) / "config.ini"
    SECTIONS = ["DEFAULT", "plotting", "board"]

    def __init__(self, c: "ConfigObj"):
        self._config = c
        logger.info(f"Init with: {c}")
        self.plotting = PlottingSection(self)
        self.board = BoardSection(self)
        self.DEFAULT = DefaultSection(self)
        self.sections = {section: getattr(self, section) for section in self.SECTIONS}
        for section_name, section in self.sections.items():
            if section_name in self._config:
                logger.info(f"[{section_name}] exist, updating with {self._config[section_name]}")
                section.update(self._config[section_name])
            else:
                logger.info(f"making empty [{section_name}]: {self.DEFAULT.to_dict()}")
                self._config[section_name] = {}

        self.write()
        self.enable_autowrite()

    def enable_autowrite(self):
        for k, v in self.sections.items():
            v.enable_autowrite()

    @classmethod
    def from_file(cls, filename):
        loaded = ConfigObj(filename)
        logger.info(f"Loaded configuration from {filename}")
        new_instance = cls(loaded)
        return new_instance

    @classmethod
    def default(cls, filename=None):
        logger.info(f"Loaded DEFAULT configuration from {str(cls.DEFAULT_CONFIG)}")
        loaded = ConfigObj(str(cls.DEFAULT_CONFIG))
        loaded.filename = filename
        new_instance = cls(loaded)
        return new_instance

    def write(self):
        if str(self._config.filename) == str(self.DEFAULT_CONFIG):
            raise ValueError(f"Cannot write into default configuration file")
        logger.info(f"Saving configuration to {self._config.filename}")
        for s in self.SECTIONS:
            self._config[s].update(getattr(self, s).to_dict())
        self._config.write()


config_dir = Path(user_config_dir(uci_cbp_demo.__appname__, uci_cbp_demo.__author__))
config_dir.mkdir(exist_ok=True, parents=True)
config_file = config_dir / "config.ini"

if config_file.is_file():
    config = Configuration.from_file(str(config_file))
else:
    config = Configuration.default(config_file)
    config.write()
