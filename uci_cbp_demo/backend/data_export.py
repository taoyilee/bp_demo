#  MIT License
#  Copyright (C) Michael Tao-Yi Lee (taoyil AT UCI EDU)
from pathlib import Path

import pandas as pd

from uci_cbp_demo.backend.bluetooth import CapData
from uci_cbp_demo.logging import logger


class FileExporterConf:
    app_data_directory = None


class FileExporterSession:
    FLUSH_EVERY_N_SAMPLES = 100

    def __init__(self, output_directory=None):
        self._output_directory = Path(output_directory)
        self._output_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Starting new FileExporterSession under {self._output_directory}")
        self.df = pd.DataFrame(
            columns=["time", "wall_clock", "cap1", "cap2",
                     "accx", "accy", "accz",
                     "gyrox", "gyroy", "gyroz",
                     "magx", "magy", "magz"])
        self.df.to_csv(self.dataframe_output, header=True, sep="\t", index=False)

    @property
    def dataframe_output(self):
        return self._output_directory / "record.tsv"

    @classmethod
    def new_session_timestamp(cls, app_data_directory):
        from datetime import datetime
        return cls(app_data_directory / datetime.now().strftime("session_%m_%d_%Y_%H_%M_%S"))

    def put(self, sample: CapData):
        logger.debug(f"{sample.to_dict()}")
        self.df = self.df.append(sample.to_dict(), ignore_index=True)
        if len(self.df) == self.FLUSH_EVERY_N_SAMPLES:
            self.df.to_csv(self.dataframe_output, mode="a", header=False, sep="\t", index=False)
            self.df = self.df.truncate(before=-1, after=-1)


class FileExporter:
    def __init__(self, conf: "FileExporterConf"):
        self._conf = conf
        self._session = None

    def put(self, sample: CapData):
        if self._session is not None:
            self._session.put(sample)

    def new_session(self):
        app_data_directory = Path(self._conf.app_data_directory)
        self._session = FileExporterSession.new_session_timestamp(app_data_directory)

    def close_session(self):
        self._session = None
