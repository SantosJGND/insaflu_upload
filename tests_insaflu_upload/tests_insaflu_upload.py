import gzip
import os
import shutil
import unittest

import pandas as pd

from insaflu_upload.insaflu_upload import (InfluDirectoryProcessing,
                                           InsafluPreMain)
from insaflu_upload.records import InfluConfig, InfluProcessed, MetadataEntry
from insaflu_upload.upload_utils import (ConnectorParamiko, InsafluSample,
                                         InsafluSampleCodes,
                                         InsafluUploadRemote, UploadLog)


class TestUploadLog(unittest.TestCase):

    def test_init(self):
        upload_log = UploadLog()

        assert upload_log.log.equals(pd.DataFrame(columns=UploadLog.columns))

    def test_new_entry(self):
        upload_log = UploadLog()

        upload_log.new_entry(
            "test",
            "test",
            "test",
            "test",
            0,
            "test",)

        assert upload_log.log.equals(pd.DataFrame(
            data=[["test", "test", "test", "test", 0, "test"]],
            columns=UploadLog.columns))


class TestInsafluUpload(unittest.TestCase):

    def test_init(self):
        pass


class TestInfluConfig(unittest.TestCase):

    def test_run_config(self):
        pass
