import gzip
import os
import shutil
import unittest

import pandas as pd

from fastq_handler.fastq_handler import DirectoryProcessing, PreMain, RunConfig
from fastq_handler.records import ProcessActionMergeWithLast, Processed
from fastq_handler.utilities import ConstantsSettings, Utils


class TestRunConfig(unittest.TestCase):

    def test_run_config(self):
        run_config = RunConfig("te", "test")

        assert run_config.output_dir == os.path.abspath("te")


class TestPreMain(unittest.TestCase):
    test_dir = "tests/"
    real_sleep = 5
    fastq_dir: str
    fastq_sbdir: str
    output_dir: str
    run_metadata: RunConfig
    premain: PreMain

    def setUp(self) -> None:

        os.makedirs(self.test_dir, exist_ok=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fastq_dir = os.path.join(self.test_dir, "fastq")
        self.fastq_sbdir = os.path.join(self.fastq_dir, "subdir")
        self.output_dir = os.path.join(self.test_dir, "output")

        if os.path.exists(self.fastq_dir):
            shutil.rmtree(self.fastq_dir)
        os.makedirs(self.fastq_dir, exist_ok=True)

        self.run_metadata = RunConfig(
            fastq_dir=self.fastq_dir,
            output_dir=self.output_dir,
            actions=[ProcessActionMergeWithLast],
            name_tag="test",
            sleep_time=self.real_sleep,
        )
        self.premain = PreMain(
            run_metadata=self.run_metadata,
        )

    def tearDown(self) -> None:

        shutil.rmtree(self.test_dir)

    def test_premain_init(self):

        processed = Processed(
            output_dir=self.run_metadata.logs_dir
        )

        assert self.premain.real_sleep == self.real_sleep
        assert self.premain.fastq_dir == self.fastq_dir
        assert self.premain.run_metadata == self.run_metadata
        assert self.premain.processed.output_dir == processed.output_dir
        assert self.premain.processed.processed.equals(
            processed.processed) is True

    def test_prep_output_dirs(self):

        self.premain.prep_output_dirs()

        assert os.path.exists(self.output_dir) is True

    def test_assess_depth_fastqs(self):

        self.premain.assess_depth_fastqs()
        assert self.premain.fastq_depth == -1

        open(os.path.join(self.fastq_dir, "test.fastq"), "w").close()

        self.premain.assess_depth_fastqs()
        assert self.premain.fastq_depth == 0
        os.remove(os.path.join(self.fastq_dir, "test.fastq"))

        os.makedirs(self.fastq_sbdir, exist_ok=True)
        open(os.path.join(self.fastq_sbdir, "test.fastq"), "w").close()

        self.premain.assess_depth_fastqs()
        assert self.premain.fastq_depth == 1

        shutil.rmtree(self.fastq_sbdir)

    def test_get_directories_to_process(self):

        assert self.premain.get_directories_to_process() == []

        open(os.path.join(self.fastq_dir, "test.fastq"), "w").close()

        self.premain.assess_depth_fastqs()
        assert self.premain.get_directories_to_process() == [self.fastq_dir]

        os.remove(os.path.join(self.fastq_dir, "test.fastq"))

        os.makedirs(self.fastq_sbdir, exist_ok=True)
        open(os.path.join(self.fastq_sbdir, "test.fastq"), "w").close()
        self.premain.assess_depth_fastqs()

        assert self.premain.get_directories_to_process() == [self.fastq_sbdir]

        shutil.rmtree(self.fastq_sbdir)

    def test_process_fastq_dict(self):
        open(os.path.join(self.fastq_dir, "test.fastq"), "w").close()

        self.premain.prep_output_dirs().assess_depth_fastqs().\
            process_fastq_dict()

        output_dir_merged = os.path.join(
            self.output_dir,
            os.path.basename(self.fastq_dir))

        output_file = f"{os.path.basename(self.fastq_dir)}_test_00-00.fastq.gz"

        assert os.path.exists(output_dir_merged) is True

        assert os.listdir(output_dir_merged) == [output_file]

        os.remove(os.path.join(self.fastq_dir, "test.fastq"))

        shutil.rmtree(self.output_dir)

        self.premain.processed.delete_records()


class DontTestConstantsSettings(unittest.TestCase):

    def test_get_seq_extentions(self):
        constants = ConstantsSettings()
        assert sorted(constants.possible_extentions) == sorted([
            ".fastq", ".fq", ".fastq.gz", ".fq.gz"])


class TestUtils(unittest.TestCase):
    test_directory = "tests/"

    def setUp(self) -> None:

        os.makedirs(self.test_directory)

    def tearDown(self) -> None:

        shutil.rmtree(self.test_directory)

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
        if os.path.exists(f"{self.test_directory}/destination"):
            shutil.rmtree(f"{self.test_directory}/destination")

        utils = Utils()

        open(f"{self.test_directory}/test.fastq", "w").close()
        utils.copy_file(f"{self.test_directory}/test.fastq",
                        f"{self.test_directory}/destination/test.fastq.gz")

        assert os.path.exists(
            f"{self.test_directory}/destination/test.fastq.gz") is True

        shutil.rmtree(f"{self.test_directory}/destination")

    def test_copy_file_gzip(self):
        if os.path.exists(f"{self.test_directory}/destination"):
            shutil.rmtree(f"{self.test_directory}/destination")

        utils = Utils()

        gzip.open(f"{self.test_directory}/test.fastq.gz", "w").close()
        utils.copy_file(f"{self.test_directory}/test.fastq.gz",
                        f"{self.test_directory}/destination/test.fastq.gz")

        assert os.path.exists(
            f"{self.test_directory}/destination/test.fastq.gz") is True

        shutil.rmtree(f"{self.test_directory}/destination")

    def test_seqs_in_dir(self):

        utils = Utils()

        os.makedirs(f"{self.test_directory}/seqs", exist_ok=True)
        assert utils.seqs_in_dir(f"{self.test_directory}/seqs") is False

        open(f"{self.test_directory}/seqs/test.fastq", "w").close()
        assert utils.seqs_in_dir(f"{self.test_directory}/seqs") is True
        os.remove(f"{self.test_directory}/seqs/test.fastq")

        os.makedirs(f"{self.test_directory}/seqs", exist_ok=True)
        assert utils.seqs_in_dir(f"{self.test_directory}/seqs") is False

    def test_seqs_in_subdir(self):

        utils = Utils()

        os.makedirs(f"{self.test_directory}/seqs", exist_ok=True)

        gzip.open(f"{self.test_directory}/seqs/test.fastq.gz", "w").close()

        assert utils.seqs_in_subdir(f"{self.test_directory}") is True

        os.remove(f"{self.test_directory}/seqs/test.fastq.gz")

    def test_get_subdirectories(self):
        utils = Utils()

        subdir_test = f"{self.test_directory}/subdir_test"

        os.makedirs(subdir_test, exist_ok=True)

        assert utils.get_subdirectories(f"{subdir_test}") == []

        os.makedirs(f"{subdir_test}/seqs", exist_ok=True)

        assert utils.get_subdirectories(f"{subdir_test}") == [
            f"{subdir_test}/seqs"]

        os.makedirs(f"{subdir_test}/seqs2", exist_ok=True)
        subdir_list = utils.get_subdirectories(f"{subdir_test}")

        assert sorted(subdir_list) == [
            f"{subdir_test}/seqs",
            f"{subdir_test}/seqs2"]

        shutil.rmtree(subdir_test)

    def test_search_folder_for_seq_files(self):

        utils = Utils()
        folder_find = f"{self.test_directory}/folder_find"
        os.makedirs(folder_find, exist_ok=True)

        assert utils.search_folder_for_seq_files(folder_find) == []

        open(f"{folder_find}/test.fastq", "w").close()

        assert utils.search_folder_for_seq_files(
            folder_find) == ["test.fastq"]


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

        self.processed.delete_records()
        processed = self.processed.read_processed()
        assert processed.empty

    def test_get_run_barcode(self):

        run_name, barcode = self.processed.get_run_barcode(
            "test.fastq", "tests/")

        processed_len = len(
            self.processed.processed[self.processed.processed.dir == "tests/"])

        assert run_name == "test"
        assert barcode == str(processed_len).zfill(2)

    def test_update(self):
        self.processed.delete_records()

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

        run_name, barcode = self.processed.get_run_info("test_00.fastq")
        assert run_name == "test_00"
        assert barcode == "00"

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
