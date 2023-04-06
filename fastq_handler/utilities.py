import itertools as it
import os
import shutil

from natsort import natsorted
from xopen import xopen


class ConstantsSettings:

    seq_extentions = [".fastq", ".fq"]
    gzip_extentions = ["", ".gz"]

    def __init__(self):

        self.possible_extentions = self.get_possible_extentions()

    def get_possible_extentions(self):

        possible_extentions = list(it.product(
            self.seq_extentions, self.gzip_extentions))
        possible_extentions = ["".join(ext) for ext in possible_extentions]

        return possible_extentions


class Utils:

    def __init__(self):
        pass

    @staticmethod
    def check_extention(file: str, possible_extentions: list):
        for ext in possible_extentions:
            if file.endswith(ext):
                return True
        return False

    @staticmethod
    def get_formated_time(seconds: int):

        hour, mins = divmod(seconds, 3600)
        mins, secs = divmod(mins, 60)

        return str(round(hour))+":"+str(round(mins))+":"+str(round(secs))

    @staticmethod
    def copy_file(input_file, destination):
        """
        copy file
        """

        if not os.path.exists(
            os.path.dirname(destination)
        ):
            os.makedirs(
                os.path.dirname(destination)
            )

        shutil.copy(input_file, destination)

    def seqs_in_dir(self, fastq_dir: str):
        """
        Check if there are any fastq files in the directory
        """
        ext = ""
        constans = ConstantsSettings()

        path_content = os.listdir(fastq_dir)

        for element in path_content:
            if os.path.isfile(
                os.path.join(fastq_dir, element)
            ):
                if self.check_extention(element, constans.possible_extentions):

                    return True

        return False

    def seqs_in_subdir(self, fastq_dir: str):
        path_content = os.listdir(fastq_dir)

        for element in path_content:
            element_path = os.path.join(fastq_dir, element)
            if os.path.isdir(element_path):
                if self.seqs_in_dir(
                    element_path
                ):
                    return True

        return False

    @staticmethod
    def get_subdirectories(fastq_dir: str):
        path_content = os.listdir(fastq_dir)

        subdirs = []
        for element in path_content:
            element_path = os.path.join(fastq_dir, element)
            if os.path.isdir(element_path):
                subdirs.append(
                    element_path
                )

        return subdirs

    def get_lattest_comp():
        pass

    #############             1 - Creating the tsv report             #############

    ##################       2 - Going through the folder       ###################

    def search_folder_for_seq_files(self, cwd: str = "."):
        """
        Lists all the files in the current work directory (cwd).

        Takes:                  Returns:
            str                     list
        """
        constants_settings = ConstantsSettings()
        possible_extentions = constants_settings.possible_extentions
        cur_files = os.listdir(cwd)

        cur_files = [file for file in cur_files if self.check_extention(
            file, possible_extentions)]

        cur_files = natsorted(cur_files)

        return cur_files

    ########################          3 - Reading          ########################

    @staticmethod
    def append_file_to_gz(filepath, filedest):
        """
        Copies the file 'filepath' to gzip file filedest."""

        try:
            with xopen(filepath, 'rb') as f_in:
                with xopen(filedest, 'ab', threads=0, compresslevel=3) as f_out:
                    shutil.copyfileobj(f_in, f_out)

        except FileNotFoundError:
            print("File not found: ", filepath)
            raise FileNotFoundError

        except KeyboardInterrupt:
            os.remove(filedest)
