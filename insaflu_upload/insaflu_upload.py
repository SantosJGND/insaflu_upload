
import os
from dataclasses import dataclass

import pandas as pd

from insaflu_upload.records import MetadataEntry
from mfmc.mfmc import DirectoryProcessing, PreMain, RunConfig
from mfmc.records import Processed


@dataclass
class InfluConfig(RunConfig):
    """
    TelevirConfig class
    """

    tsv_temp_name: str = "televir_metadata.tsv"
    metadata_dir: str = "metadata_dir"


class InfluProcessed(Processed):
    """
    TelevirProcessed class
    """

    def __init__(self, output_dir: str):
        super().__init__(output_dir)

    def generate_metadata_entry_row(self, row: pd.Series):
        """
        create tsv
        """
        fastq_dir = row.dir
        fastq_file = row.fastq
        merged_file = row.merged

        new_entry = self.generate_metadata_entry(
            fastq_file, fastq_dir, merged_file)

        return new_entry

    def generate_metadata_entry(self, fastq_file: str, fastq_dir: str, merged_file: str):

        proj_name, barcode = self.get_run_barcode(
            fastq_file, fastq_dir)

        time_elapsed = self.get_file_time(
            fastq_file=fastq_file,
            fastq_dir=fastq_dir
        )

        # Create the metadata entry
        new_entry = MetadataEntry(
            sample_name=proj_name,
            fastq1=merged_file,
            time_elapsed=time_elapsed,
            dir=os.path.dirname(merged_file)
        )

        return new_entry.export_as_dataframe()

    def generate_metadata(self):
        """
        create tsv
        """
        metadata = pd.DataFrame()

        for index, row in self.processed.iterrows():
            metadata = pd.concat(
                [metadata, self.generate_metadata_entry_row(row)])

        return metadata


class InfluDirectoryProcessing(DirectoryProcessing):
    """
    TelevirDirectoryProcessing class
    replace directory gen to include metadata
    """

    metadata_suffix: str = "_metadata.tsv"
    metadata_dirname = "metadata_dir"

    def __init__(self, fastq_dir: str, run_metadata: InfluConfig, processed: InfluProcessed, start_time: float):
        super().__init__(fastq_dir, run_metadata, processed, start_time)

        self.run_metadata = run_metadata
        self.processed = processed

        self.metadir = os.path.join(
            self.run_metadata.metadata_dir,
            os.path.basename(fastq_dir.strip("/")),
            self.metadata_dirname,
        )

    def prep_output_dirs(self):
        """create output dirs"""

        for dir in [
            self.merged_gz_dir,
            self.metadir,
        ]:
            os.makedirs(dir, exist_ok=True)

    @staticmethod
    def get_filename_from_path(file_name):
        filename = os.path.basename(file_name)
        filename, ext = os.path.splitext(filename)
        if ext == ".gz":
            filename, ext = os.path.splitext(filename)
        return filename

    def metadata_name_for_sample(self, sample_name):
        filename = self.get_filename_from_path(sample_name)

        return filename + self.metadata_suffix

    def write_metadata(self, fastq_file: str, fastq_dir: str, merged_gz_file: str):
        """
        update metadata
        """
        filename = self.metadata_name_for_sample(fastq_file)
        new_entry = self.processed.generate_metadata_entry(
            fastq_file, fastq_dir, merged_gz_file)

        new_entry.to_csv(
            os.path.join(
                self.metadir,
                filename
            ),
            sep="\t",
            index=False,
        )

    def process_file(self, fastq_file):

        merged_file = self.create_merged_file(fastq_file, self.fastq_dir)

        self.update_processed(fastq_file, self.fastq_dir,
                              merged_file)

        self.write_metadata(fastq_file, self.fastq_dir, merged_file)


class InsafluUpload(PreMain):
    """
    InsafluUpload class
    """

    processed: InfluProcessed
    run_metadata: InfluConfig

    def __init__(self, fastq_dir: str, run_metadata: InfluConfig, sleep_time: int):
        super().__init__(fastq_dir, run_metadata, sleep_time)

        self.processed = InfluProcessed(
            self.run_metadata.output_dir,
        )

        self.run_metadata = run_metadata

    def get_directory_processing(self, fastq_dir: str):
        return InfluDirectoryProcessing(fastq_dir, self.run_metadata, self.processed, self.start_time)

    def prep_metadata_dir(self):
        """
        create output directories
        """

        os.makedirs(self.run_metadata.metadata_dir, exist_ok=True)

    def export_global_metadata(self):

        influ_metadata = self.processed.generate_metadata()

        influ_metadata.to_csv(
            os.path.join(
                self.run_metadata.metadata_dir,
                self.run_metadata.tsv_temp_name
            ),
            sep="\t",
            index=False,
        )

    def run(self):
        super().run()
        self.prep_metadata_dir()
        self.export_global_metadata()
