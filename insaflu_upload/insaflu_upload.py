
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

    def televir_process_file(self, fastq_file):

        merged_file = self.get_merged_file_name(fastq_file, self.fastq_dir)

        new_entry = self.write_metadata(
            fastq_file, self.fastq_dir, merged_file)

        self.upload_sample(new_entry)
        self.submit_sample(new_entry)

    def process_folder(self):
        """
        process folder
        """

        self.prep_output_dirs()
        files_to_process = self.get_files()

        for ix, fastq_file in enumerate(files_to_process):
            self.process_file(fastq_file)

            if ix == len(files_to_process) - 1:
                self.televir_process_file(
                    fastq_file
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

    def logger_iterate(self, iterator):
        """
        iterate over iterator and log
        """
        for item in iterator:
            self.logger.info("processing %s", item)
            yield item

    def process_samples(self):
        """
        process samples
        """

        combined = self.uploader.logger.get_log().reset_index(drop=True)

        for sample_id, sample_df in combined.groupby("sample_id"):

            file_path = sample_df[sample_df.tag ==
                                  "fastq"]["file_path"].values[0]

            file_name, _ = self.processed.get_run_info(file_path)
            project_name = sample_id

            status = self.uploader.update_sample_status_remote(
                file_name, file_path)

            if status == InsafluSampleCodes.STATUS_UPLOADED:

                ###
                status = self.uploader.deploy_televir_sample(
                    sample_id,
                    file_name,
                    file_path,
                    project_name,
                )

            if status == InsafluSampleCodes.STATUS_SUBMITTED:

                project_file = self.uploader.get_project_results(
                    project_name,
                )

                self.uploader.download_file(
                    project_file, os.path.join(
                        self.run_metadata.metadata_dir,
                        os.path.basename(project_file),
                    )
                )

    def combined_processed_uploadlog(self):
        """
        combine processed and upload log
        """

        logs = self.run_metadata.uploader.logger.get_log().reset_index(drop=True)
        print("#######3")
        print(logs)

        # get tag from logs into processed
        processed_tag = self.processed.processed.reset_index(drop=True)
        print(processed_tag)

        # get tag by mapping file_path to logs
        processed_tag["tag"] = processed_tag["merged"].map(
            logs.set_index("file_path")["tag"]
        )

        # get status by mapping file_path to logs
        processed_tag["status"] = processed_tag["merged"].map(
            logs.set_index("file_path")["status"]
        )

        combined = (self.processed.processed.merge(
            logs, left_on="merged", right_on="sample_id", how="outer")
            .rename(columns={"barcode_x": "barcode"})
            .dropna(subset=["barcode"]))

        print(combined)

        return combined

    def run(self):
        super().run()
        self.process_samples()
        self.export_global_metadata()
