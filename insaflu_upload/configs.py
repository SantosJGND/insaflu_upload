
import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional, Type

from fastq_handler.records import InputState, OutputDirs, RunParams
from insaflu_upload.tables_post import InsafluTables
from insaflu_upload.upload_utils import InsafluUpload, UploadStrategy

default_log_handler = logging.StreamHandler(sys.stdout)
default_log_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(message)s')
default_log_handler.setFormatter(formatter)


@dataclass
class InfluParams(RunParams):
    """
    class to hold parameters with defaults
    """
    deploy_televir: bool = False
    monitor: bool = False


@dataclass
class InfluUpload(InputState):
    """
    class to hold input
    """
    uploader: Optional[InsafluUpload] = None
    upload_strategy: Optional[Type[UploadStrategy]] = None


@dataclass
class InfluOutput(OutputDirs):
    tsv_temp_name: str = "televir_metadata.tsv"
    metadata_dirname: str = "metadata_dir"
    logs_dirname: str = "logs"
    db_path: str = "insaflu.db"


@dataclass
class InfluConfig(InfluParams, InfluUpload, InfluOutput):
    """
    TelevirConfig class
    """

    def __post_init__(self):

        self.name_tag = self.name_tag.strip()
        self.uploader = self.uploader
        self.upload_strategy = self.upload_strategy
        self.actions = self.actions

        self.keep_name = self.keep_name
        self.deploy_televir = self.deploy_televir

        self.metadata_dir = os.path.join(
            self.output_dir, self.metadata_dirname)

        self.logs_dir = os.path.join(self.output_dir, self.logs_dirname)
        self.db_path = os.path.join(self.logs_dir, self.db_path)

        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        self.tables = InsafluTables(self.db_path)
        self.tables.setup()
