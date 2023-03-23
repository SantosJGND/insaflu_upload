import gzip
import os
import shutil
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import mockssh
import pandas as pd
import paramiko
import pytest
from paramiko import SSHClient

from insaflu_upload.insaflu_upload import (InfluDirectoryProcessing,
                                           InsafluPreMain)
from insaflu_upload.records import InfluConfig, InfluProcessed, MetadataEntry
from insaflu_upload.upload_utils import (ConnectorParamiko, InsafluFile,
                                         InsafluSampleCodes,
                                         InsafluUploadRemote, UploadLog)


@pytest.fixture(scope="session")
def temp_config_file(tmp_path_factory):
    config_file = tmp_path_factory.mktemp("config") / "config.ini"

    with open(config_file, "w") as f:

        f.write(
            """
            [SSH]
            username = localhost
            ip_address = 127.0.0.1
            rsa_key = /home/bioinf/.ssh/id_rsa
            """
        )

    return config_file


class TestUploadLog(unittest.TestCase):

    def test_init(self):
        upload_log = UploadLog()

        assert upload_log.log.equals(pd.DataFrame(columns=UploadLog.columns))

    def test_new_entry(self):
        upload_log = UploadLog()

        new_entry = pd.concat(
            [
                upload_log.log,
                pd.DataFrame(
                    data=[["test", "test", "test", "test", 0, "test"]],
                    columns=UploadLog.columns)
            ]
        )

        upload_log.new_entry(
            "test",
            "test",
            "test",
            "test",
            0,
            "test",)

        assert upload_log.log.equals(new_entry)

    def test_modify_entry_status(self):
        upload_log = UploadLog()

        upload_log.new_entry(
            "test",
            "test",
            "test",
            "test",
            0,
            "test",)

        upload_log.modify_entry_status("test", 2)

        assert upload_log.log.loc[0, "status"] == 2

    def test_update_log_existing(self):
        upload_log = UploadLog()

        upload_log.new_entry(
            "test",
            "test",
            "test",
            "test",
            0,
            "test",)

        upload_log.update_log("test", "test", "test", "test", 2)

        assert upload_log.log.loc[0, "status"] == 2

    def test_check_entry_exists(self):

        upload_log = UploadLog()

        upload_log.new_entry(
            "test",
            "test",
            "test",
            "test",
            0,
            "test",)

        assert upload_log.check_entry_exists("test") == True

    def test_update_log_new(self):
        upload_log = UploadLog()

        upload_log.new_entry(
            "test1",
            "test1",
            "test1",
            "test1",
            0,
            "test1",)

        upload_log.update_log("test", "test", "test", "test", 2)

        assert upload_log.check_entry_exists("test") == True

    def test_get_log(self):

        upload_log = UploadLog()

        assert upload_log.get_log().equals(pd.DataFrame(columns=UploadLog.columns))

    def get_file_status(self):

        upload_log = UploadLog()

        upload_log.new_entry(
            "test",
            "test",
            "test",
            "test",
            0,
            "test",)

        assert upload_log.get_file_status("test") == "test"

    def test_generate_InsafluSample(self):

        upload_log = UploadLog()

        upload_log.new_entry(
            "test",
            "test",
            "test",
            "test",
            0,
            "test",)

        sample = upload_log.generate_InsafluFile(
            upload_log.log.loc[0],
        )

        assert sample.sample_id == "test"
        assert sample.barcode == "test"
        assert sample.file_path == "test"
        assert sample.remote_path == "test"
        assert sample.status == 0

    def test_get_sample(self):
        upload_log = UploadLog()

        upload_log.new_entry(
            "test",
            "test",
            "test",
            "test",
            0,
            "fastq",)

        sample_files = upload_log.get_sample_files("test")
        sample = sample_files[0]
        assert sample.sample_id == "test"
        assert sample.barcode == "test"
        assert sample.file_path == "test"
        assert sample.remote_path == "test"
        assert sample.status == 0

    def get_sample_remotepaths(self):
        upload_log = UploadLog()

        upload_log.new_entry(
            "test",
            "test",
            "test",
            "test",
            0,
            "fastq",)

        sample_files = upload_log.get_sample_remotepaths("test")
        sample = sample_files[0]
        assert sample == "test"

    def test_get_samples_list(self):
        """
        test get_samples_list"""
        upload_log = UploadLog()

        upload_log.new_entry(
            "test",
            "test",
            "test",
            "test",
            0,
            "fastq",)

        sample_list = upload_log.generate_samples_list()

        sample = sample_list[0]
        assert sample.sample_id == "test"


class ConnectorParamikoProxy(ConnectorParamiko):

    def connect(self):
        """
        create local ssh mock server"""
        users = {
            "test-user": "/home/bioinf/.ssh/id_rsa",
        }
        self.server = mockssh.Server(users)

    def __enter__(self):
        self.server.__enter__()
        with self.server as s:
            self.conn = s.client("test-user")
            return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.server.__exit__(exc_type, exc_value, traceback)


class TestConnectorParamiko:

    def test_init(self, tmpdir):

        config_file = tmpdir.mkdir("config").join("config.ini")

        config_file.write(
            """
            [SSH]
            username = localhost
            ip_address = 127.0.0.1
            rsa_key = /home/bioinf/.ssh/id_rsa
            """
        )
        connector = ConnectorParamikoProxy(config_file=config_file)

        assert connector.username == "localhost"
        assert connector.ip_address == "127.0.0.1"
        assert connector.rsa_key_path == "/home/bioinf/.ssh/id_rsa"

    def test_check_file_exists(self, tmpdir, temp_config_file):
        """
        test check_file_exists method"""
        connector = ConnectorParamikoProxy(config_file=temp_config_file)

        assert connector.check_file_exists("test") == False

        temp_file = tmpdir.mkdir("temp").join("temp.txt")

        temp_file.write("test")

        assert connector.check_file_exists(temp_file) == True

    def test_execute_command(self, tmpdir, temp_config_file):
        """
        test execute_command method"""
        connector = ConnectorParamikoProxy(config_file=temp_config_file)

        assert connector.execute_command("echo test").strip() == "test"

    def test_download_file(self, tmpdir, temp_config_file):
        """
        test download_file method"""
        connector = ConnectorParamikoProxy(config_file=temp_config_file)

        tmpdir = tmpdir.mkdir("temp")
        temp_file = tmpdir.join("temp.txt")
        output_file = tmpdir.join("output.txt")

        temp_file.write("test")

        connector.download_file(str(temp_file), str(output_file))

        assert output_file.read() == "test"

    def test_upload_file(self, tmpdir, temp_config_file):
        """
        test upload_file method"""
        connector = ConnectorParamikoProxy(config_file=temp_config_file)

        tmpdir = tmpdir.mkdir("temp")
        temp_file = tmpdir.join("temp.txt")
        output_file = tmpdir.join("output.txt")

        temp_file.write("test")

        connector.upload_file(str(temp_file), str(output_file))

        assert output_file.read() == "test"
