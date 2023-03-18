import os
import shutil
import unittest

import pandas as pd

from mfmc.records import Processed
from mfmc.utilities import ConstantsSettings, Utils


class TestConstantsSettings(unittest.TestCase):

    def test_get_seq_extentions(self):
        constants = ConstantsSettings()
        assert constants.possible_extentions == [
            ".fastq", ".fq", ".fastq.gz", ".fq.gz"]


class TestUtils(unittest.TestCase):

    def test_check_extention(self):
        utils = Utils()
        assert utils.check_extention("test.fastq", [
            ".fastq", ".fq", ".fastq.gz", ".fq.gz"]) is True
        assert utils.check_extention("test.fastq.gz", [
            ".fastq", ".fq", ".fastq.gz", ".fq.gz"]) is True
        assert utils.check_extention("test.fq", [
            ".fastq", ".fq", ".fastq.gz", ".fq.gz"]) is True
        assert utils.check_extention("test.fq.gz", [
            ".fastq", ".fq", ".fastq.gz", ".fq.gz"]) is True

        assert utils.check_extention("test.fa", [
            ".fastq", ".fq", ".fastq.gz", ".fq.gz"]) is False
        assert utils.check_extention("test.fa.gz", [
            ".fastq", ".fq", ".fastq.gz", ".fq.gz"]) is False
        assert utils.check_extention("test.txt", [
            ".fastq", ".fq", ".fastq.gz", ".fq.gz"]) is False
        assert utils.check_extention("test.txt.gz", [
            ".fastq", ".fq", ".fastq.gz", ".fq.gz"]) is False

    def test_get_formated_time(self):
        utils = Utils()
        assert utils.get_formated_time(0) == "0:0:0"
        assert utils.get_formated_time(1) == "0:0:1"
        assert utils.get_formated_time(60) == "0:1:0"
        assert utils.get_formated_time(3600) == "1:0:0"
        assert utils.get_formated_time(3601) == "1:0:1"
        assert utils.get_formated_time(3661) == "1:1:1"
        assert utils.get_formated_time(86400) == "24:0:0"

    def test_copy_file(self):
        if os.path.exists("tests/destination"):
            shutil.rmtree("tests/destination")

        utils = Utils()
        utils.copy_file("tests/test.fastq", "tests/destination/test.fastq.gz")

        assert os.path.exists("tests/destination/test.fastq") is True

        shutil.rmtree("tests/destination")


class TestProcessed(unittest.TestCase):
    test_directory = "tests/"

    def setup(self):
        if os.path.exists(f"{self.test_directory}processed.tsv"):
            os.remove(f"{self.test_directory}processed.tsv")

        self.processed = Processed(self.test_directory)

    def __init__(self, *args, **kwargs):
        super(TestProcessed, self).__init__(*args, **kwargs)
        self.setup()

    def teardown(self):
        shutil.rmtree(self.test_directory)

    def test_init(self):
        assert self.processed.output_dir == self.test_directory
        assert self.processed.output_file == "processed.tsv"

    def test_read_processed(self):
        processed_file = os.path.join(
            self.processed.output_dir,
            self.processed.output_file
        )

        self.processed.delete_records()
        processed = self.processed.read_processed()
        assert processed.empty

    def test_get_run_barcode(self):

        run_name, barcode = self.processed.get_run_barcode(
            "test.fastq", "tests/")

        processed_len = len(self.processed.processed)

        assert run_name == "test"
        assert barcode == str(processed_len).zfill(2)

    def test_update(self):
        print("!@#$%^&*()_+")

        self.processed.update("test.fastq", "tests/", 0, "merged.fastq")

        assert self.processed.processed.empty is False
        assert self.processed.processed.loc[0, "fastq"] == "test.fastq"
        assert self.processed.processed.loc[0, "dir"] == "tests/"
        assert self.processed.processed.loc[0, "barcode"] == "00"
        assert self.processed.processed.loc[0, "time"] == 0
        assert self.processed.processed.loc[0, "merged"] == "merged.fastq"
        self.processed.delete_records()

    def test_delete_records(self):
        self.processed.delete_records()
        assert self.processed.processed.empty

    def test_get_file_time(self):

        self.processed.update("test.fastq", "tests/", 0, "merged.fastq")
        assert self.processed.get_file_time("test.fastq", "tests/") == 0
        self.processed.delete_records()

    def test_get_dir_merged_last(self):

        self.processed.update("test.fastq", "tests/", 0, "merged.fastq")
        self.processed.update("test2.fastq", "tests/", 1, "merged2.fastq")

        assert self.processed.get_dir_merged_last("tests/") == "merged2.fastq"
        self.processed.delete_records()

    def test_get_run_info(self):

        run_name, barcode = self.processed.get_run_info("test.fastq")
        assert run_name == "test"
        assert barcode == ""

    def test_file_exists(self):

        self.processed.processed = pd.DataFrame(
            columns=[
                "fastq",
                "dir",
                "barcode",
                "time",
                "merged",
            ]
        )
        self.processed.processed.loc[0] = [
            "test.fastq", "tests/", "barcode", 0, False]
        assert self.processed.file_exists("test.fastq", "tests/") == True
        self.processed.delete_records()
