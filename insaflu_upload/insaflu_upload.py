
import logging
import os
from dataclasses import dataclass

from insaflu_upload.records import InfluConfig, InfluProcessed, MetadataEntry
from insaflu_upload.upload_utils import InsafluSampleCodes, InsafluUpload
from mfmc.mfmc import DirectoryProcessing, PreMain


class InfluDirectoryProcessing(DirectoryProcessing):
    """
    TelevirDirectoryProcessing class
    replace directory gen to include metadata
    """

    metadata_suffix: str = "_metadata.tsv"
    metadata_dirname = "metadata_dir"
    uploader: InsafluUpload

    def __init__(self, fastq_dir: str, run_metadata: InfluConfig, processed: InfluProcessed,
                 start_time: float):
        super().__init__(fastq_dir, run_metadata, processed, start_time)

        self.run_metadata = run_metadata
        self.processed = processed
        self.uploader = run_metadata.uploader

        self.metadir = os.path.join(
            self.run_metadata.metadata_dir,
            os.path.basename(fastq_dir.strip("/")),
            self.metadata_dirname,
        )

    def prep_output_dirs(self):
        """create output dirs"""

        for outdir in [
            self.merged_gz_dir,
            self.metadir,
        ]:
            os.makedirs(outdir, exist_ok=True)

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
        metadata_entry = self.processed.generate_metadata_entry(
            fastq_file, fastq_dir, merged_gz_file)

        metadata_filename = self.metadata_name_for_sample(
            metadata_entry.fastq1)

        metadata_entry.export_as_dataframe().to_csv(
            os.path.join(
                self.metadir,
                metadata_filename
            ),
            sep="\t",
            index=False,
        )

        return metadata_entry

    def upload_sample(self, metadata_entry: MetadataEntry):
        """
        upload sample to remote server"""

        metadata_filename = self.metadata_name_for_sample(
            metadata_entry.fastq1)

        metadata_path = os.path.join(
            self.metadir,
            metadata_filename
        )

        _, barcode = self.processed.get_run_barcode(
            metadata_entry.fastq1, self.metadir)

        sample_id = self.processed.get_sample_id_from_merged(
            metadata_entry.fastq1
        )

        self.uploader.upload_sample(
            metadata_entry.r1_local,
            metadata_path,
            sample_id=sample_id,
            barcode=barcode,
        )

    def submit_sample(self, metadata_entry: MetadataEntry):
        """
        submit sample to remote server"""

        metadata_filename = self.metadata_name_for_sample(
            metadata_entry.fastq1)

        insaflu_metadata_file = os.path.join(
            self.metadir,
            metadata_filename
        )

        self.uploader.submit_sample(
            insaflu_metadata_file,
        )

    def televir_process_file(self, fastq_file, merged_file):
        """
        process file for televir, upload and submit"""

        new_entry = self.write_metadata(
            fastq_file, self.fastq_dir, merged_file)

        self.upload_sample(new_entry)
        self.submit_sample(new_entry)

    def process_file(self, fastq_file):
        """
        process file, merge and update metadata"""

        merged_file = self.create_merged_file(fastq_file, self.fastq_dir)

        self.update_processed(fastq_file, self.fastq_dir,
                              merged_file)

        return merged_file

    def process_folder(self):
        """
        process folder, merge and update metadata
        submit to televir only the last file.
        """

        self.prep_output_dirs()
        files_to_process = self.get_files()

        for ix, fastq_file in enumerate(files_to_process):
            merged_file = self.process_file(fastq_file)

            if ix == len(files_to_process) - 1:
                self.televir_process_file(
                    fastq_file, merged_file
                )


class InsafluPreMain(PreMain):
    """
    InsafluUpload class
    """

    processed: InfluProcessed
    run_metadata: InfluConfig

    def __init__(self, fastq_dir: str, run_metadata: InfluConfig, sleep_time: int):
        super().__init__(fastq_dir, run_metadata, sleep_time)

        self.processed = InfluProcessed(
            self.run_metadata.metadata_dir,
        )

        self.uploader = run_metadata.uploader

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.run_metadata = run_metadata

    def get_directory_processing(self, fastq_dir: str):

        return InfluDirectoryProcessing(fastq_dir, self.run_metadata, self.processed,
                                        self.start_time)

    def prep_metadata_dir(self):
        """
        create output directories
        """

        os.makedirs(self.run_metadata.metadata_dir, exist_ok=True)

    def export_global_metadata(self):

        self.prep_metadata_dir()
        self.processed.export_metadata(
            self.run_metadata
        )

    def process_samples(self):
        """
        process samples
        """

        samples_list = self.uploader.logger.generate_samples_list()

        for sample in samples_list:
            project_name = sample.sample_id

            file_name, _ = self.processed.get_run_info(sample.file_path)

            status = self.uploader.update_sample_status_remote(
                file_name, sample.file_path)

            if status == InsafluSampleCodes.STATUS_UPLOADED:

                status = self.uploader.deploy_televir_sample(
                    sample.sample_id,
                    file_name,
                    sample.file_path,
                    project_name,
                )

            if status == InsafluSampleCodes.STATUS_SUBMITTED:

                self.uploader.get_project_results(
                    project_name, self.run_metadata.metadata_dir
                )

    def run(self):
        super().run()
        self.process_samples()
        self.export_global_metadata()
