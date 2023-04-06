# -*- coding: utf-8 -*-
"""
Created on Fri Feb 17 14:20:20 2023

@author: andre
"""

import os
import subprocess
import sys
import time

import pandas as pd

from fastq_handler.records import Processed, RunConfig
from fastq_handler.utilities import Utils

pd.options.mode.chained_assignment = None  # default='warn'


"""
Notes:
- Now automatically detects if there's barcoding or not and also the format.
- Now it always creates .fastq.gz merged files.

TO DO:
- de sleep em sleep fazer uma pasta com 'lattest_compilation_to_upload' todos os últimos concatenados por amostra
(barcode10, barcode11, etc) + um ficheiro de metadata com todos os dados respetivos dos concatenados totais.

"""

HELP = " _________________________________________________\n | mfmc.py - MERGING FASTQ AND METADATA CREATION | \n _________________________________________________\nExample of usage:\npython mfmc.py --in_dir C:\\users\\samples --out_dir C:\\users\processed_files --tsv_t_name template.tsv --tsv_t_dir C:\\users\\templates \n\nOptions and arguments:\n--in_dir [DIRECTORY OF THE FAST_PASS] : directory of the files being produced by the sequencing machine (typically the 'fast_pass' folder).\n--out_dir [OUTPUT DIRECTORY or 'q' for the default] : desired directory to storage the output files\n--tsv_t_n [TSV TEMPLATE FILE NAME] : name of the tsv template\n--tsv_t_dir [TSV TEMPLATE DIRECTORY] : directory of the tsv template file\n--sleep [TIME SLEEP] : amount of time (in seconds) for the script to hold, between search cycles"
ARGUMENT_OPTIONS = ["--in_dir", "--out_dir", "--tsv_t_n", "--tsv_t_dir"]


####################         5 - Main functions          #####################


class PreMain:

    start_time: float
    folder_files: list = []

    fastq_dir: str
    start_time: float
    real_sleep: int = 5
    fastq_depth: int = -1

    processed: Processed
    fastq_avail: pd.DataFrame = pd.DataFrame()

    def __init__(
        self,
        run_metadata: RunConfig,

    ):
        self.fastq_dir = run_metadata.fastq_dir
        self.run_metadata = run_metadata
        self.start_time = time.time()
        self.real_sleep = run_metadata.sleep_time

        self.processed = Processed(
            output_dir=self.run_metadata.logs_dir)

        self.log_dir = os.path.join(
            self.run_metadata.logs_dir,
        )

    def prep_output_dirs(self):
        """
        create output directories
        """
        os.makedirs(self.run_metadata.output_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        return self

    def assess_depth_fastqs(self):

        utils = Utils()
        fastq_depth = -1

        if utils.seqs_in_dir(self.fastq_dir):
            fastq_depth = 0

        if utils.seqs_in_subdir(self.fastq_dir):
            fastq_depth = 1

        self.fastq_depth = fastq_depth

        return self

    def assess_proceed(self):
        """
        assess if proceed
        """
        if self.fastq_depth == -1:
            print("No fastq files found in: ", self.fastq_dir)

        return self

    def get_directories_to_process(self):
        """
        get directories to process
        """

        utils = Utils()

        if self.fastq_depth == 0:
            return [self.fastq_dir]

        else:
            return utils.get_subdirectories(self.fastq_dir)

    def get_directory_processing(self, fastq_dir: str):
        return DirectoryProcessingSimple(fastq_dir, self.run_metadata, self.processed, self.start_time)

    def process_fastq_dict(self):
        """
        process fastq dict
        """
        for fastq_dir in self.get_directories_to_process():
            directory_processing = self.get_directory_processing(
                fastq_dir=fastq_dir,
            )

            directory_processing.process_folder()

        return self

    def run(self):
        """
        run single pass
        """
        (self.prep_output_dirs()
         .assess_depth_fastqs()
         .assess_proceed()
         .process_fastq_dict())

        self.processed.export(
            self.run_metadata.logs_dir
        )

    def run_until_killed(self):
        """
        run until killed
        """
        try:
            while True:
                self.run()
                print("Sleeping for: ", self.real_sleep, " seconds")
                time.sleep(self.real_sleep)

        except KeyboardInterrupt:

            print("KeyboardInterrupt")
            return


class DirectoryProcessing():
    """
    class to process a directory
    copies all files to a single directory. checks if already processed.
    creates directory specific output subdirectory in output directory.
    """

    merged_dir_name = "merged_files"
    outfiles_dir_name = "out_files"

    def __init__(self, fastq_dir: str, run_metadata: RunConfig, processed: Processed, start_time: float):
        self.fastq_dir = fastq_dir
        self.run_metadata = run_metadata
        self.start_time = start_time
        self.processed = processed

        self.merged_gz_dir = os.path.join(
            self.run_metadata.output_dir,
            os.path.basename(self.fastq_dir.strip("/")),)

    def time_since_start(self):
        """
        returns the time since the start of the program
        """
        return time.time() - self.start_time

    def prep_output_dirs(self):
        """create output dirs"""

        for dir in [
            self.merged_gz_dir,
        ]:
            os.makedirs(dir, exist_ok=True)

    def match_to_processed(self, fastq_file, fastq_dir):
        """
        match to process dict
        """

        return self.processed.file_exists(
            fastq_file=fastq_file,
            fastq_dir=fastq_dir
        )

    @staticmethod
    def check_file_open_linux(file_path):
        """
        check if file is open
        """
        command = f"lsof -t {file_path} | wc -l"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()

        output = output.decode("utf-8").strip()

        return int(output) > 1

    def check_file_open_windows(self, file_path):
        """
        check if file is open
        """
        return True

    def check_file_open(self, file_path):
        """
        check if file is open
        """

        platform = sys.platform

        if platform == "linux":
            return self.check_file_open_linux(file_path)

        elif platform == "win32":
            return self.check_file_open_windows(file_path)

        return True

    def check_file_for_process(self, fastq_file, fastq_dir):
        """
        check if file is open
        """

        file_path = os.path.join(
            fastq_dir,
            fastq_file)

        if not os.path.isfile(file_path):
            return False

        if self.match_to_processed(fastq_file, fastq_dir):
            return False

        return False if self.check_file_open(file_path) else True

    def get_files(self):
        """
        get folders and files
        """

        utils = Utils()

        folder_files = utils.search_folder_for_seq_files(self.fastq_dir)
        folder_files = [
            x for x in folder_files if self.check_file_for_process(x, self.fastq_dir)]

        if folder_files == []:
            print("No new files in ", self.fastq_dir)

        folder_files = [os.path.join(self.fastq_dir, x) for x in folder_files]

        return folder_files

    def append_to_file(self, fastq_file, destination_file):
        """
        append to file
        """
        utils = Utils()

        utils.append_file_to_gz(
            fastq_file, destination_file
        )

    def get_merged_file_name(self, fastq_file, fastq_dir):

        _, run_num = self.processed.get_run_barcode(
            fastq_file, fastq_dir)

        merged_name_prefix = os.path.basename(os.path.dirname(fastq_file))

        first_run_barcode = self.processed.get_dir_barcode_first(fastq_dir)
        if first_run_barcode == "":
            first_run_barcode = run_num

        if self.run_metadata.name_tag:
            merged_name_prefix = f"{merged_name_prefix}_{self.run_metadata.name_tag}"

        merged_name = f"{merged_name_prefix}_{first_run_barcode}-{run_num}.fastq.gz"

        merged_name = os.path.join(self.merged_gz_dir, merged_name)

        return merged_name

    def prep_merged_file(self, fastq_file, fastq_dir):
        """
        get merged name
        """
        utils = Utils()

        merged_name = self.get_merged_file_name(fastq_file, fastq_dir)

        open(merged_name, 'a').close()

        return merged_name

    def update_processed(self, fastq_file, fastq_dir, merged_file):
        """
        update processed
        """

        time_elapsed = self.time_since_start()

        self.processed.update(
            fastq_file=fastq_file,
            fastq_dir=fastq_dir,
            time_elapsed=time_elapsed,
            merged_file=merged_file
        )

    def read_tsv_template(self, template_tsv) -> pd.DataFrame:
        """
        read tsv template
        """

        try:
            template_tsv = pd.read_csv(
                template_tsv, sep='\t')

        except FileNotFoundError:
            template_tsv = pd.DataFrame(
                columns=["sample name", "fastq1", "time elapsed"])

        return template_tsv

    def set_destination_filepath(self, fastq_file, fastq_dir):
        """
        set destination filepath"""

        if self.run_metadata.keep_name:
            return os.path.join(
                self.merged_gz_dir,
                os.path.basename(fastq_file)
            )

        else:
            return self.get_merged_file_name(fastq_file, fastq_dir)


class DirectoryProcessingSimple(DirectoryProcessing):
    """
    class to process a directory
    copies all files to a single directory. checks if already processed.
    creates directory specific output subdirectory in output directory.
    """

    merged_dir_name = "merged_files"
    outfiles_dir_name = "out_files"

    def __init__(self, fastq_dir: str, run_metadata: RunConfig, processed: Processed, start_time: float):
        super().__init__(fastq_dir, run_metadata, processed, start_time)

    def process_file(self, fastq_file: str):

        destination_file = fastq_file

        if self.run_metadata.actions:
            destination_file = self.set_destination_filepath(
                fastq_file, self.fastq_dir)

            self.append_to_file(fastq_file, destination_file)

            sample_id = self.processed.get_sample_id_from_merged(
                destination_file)

            for process_action in self.run_metadata.actions:

                process_action.process(
                    destination_file, sample_id, self.processed)

        self.update_processed(fastq_file, self.fastq_dir,
                              destination_file)

        return self

    def local_process(self):

        files_to_process = self.get_files()

        for ix, fastq_file in enumerate(files_to_process):
            self.process_file(fastq_file)

    def process_folder(self):
        """
        process folder, merge and update metadata
        submit to televir only the last file.
        """
        self.prep_output_dirs()
        self.local_process()

############################ SYSTEM STUFF ##########################

# TESTING

# # print("barcoding on and gz")
# minion_file_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_automatic\\test_fastq_gz_bar\\fastq_gz_barcoding"
# output_dir="q"
# # output_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# tsv_temp_name="template_metadata.tsv"
# tsv_temp_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# main(minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir, sleep_time=5)


# # print("barcoding off and gz")
# minion_file_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_automatic\\test_fastq_gz_n_bar\\fastq_gz_n_barcoding"
# output_dir="q"
# # output_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# tsv_temp_name="template_metadata.tsv"
# tsv_temp_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# main(minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir, sleep_time=5)


# # print("barcoding on and fastq")
# minion_file_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_automatic\\test_fastq_bar\\fastq_barcoding"
# output_dir="q"
# # output_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# tsv_temp_name="template_metadata.tsv"
# tsv_temp_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# main(minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir, sleep_time=5)


# # print("barcoding off and fastq")
# minion_file_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\1º Ano\\2º Semestre\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_automatic\\test_fastq_n_bar\\fastq_n_barcoding"
# output_dir="q"
# # output_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\2º Ano\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# tsv_temp_name="template_metadata.tsv"
# tsv_temp_dir="C:\\Users\\andre\\OneDrive - FCT NOVA\\André\\Mestrado - Bioinfo\\1º Ano\\2º Semestre\\Projeto em Multi-Ómicas - INSA\\teste_1\\testing_files\\testing_merging_and_metadata_files\\barcoded_samples"
# main(minion_file_dir, output_dir, tsv_temp_name, tsv_temp_dir, sleep_time=5)
