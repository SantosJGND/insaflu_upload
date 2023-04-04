
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from insaflu_upload.plot_utils import plot_project_results
from insaflu_upload.records import InfluConfig, InfluProcessed, MetadataEntry
from insaflu_upload.upload_utils import InsafluSampleCodes, InsafluUpload
from mfmc.mfmc import DirectoryProcessingSimple, PreMain


class InfluDirectoryProcessing(DirectoryProcessingSimple):
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

    def register_sample(self, metadata_entry: MetadataEntry):
        """
        register sample to remote server"""

        metadata_filename = self.metadata_name_for_sample(
            metadata_entry.fastq1)

        metadata_path = os.path.join(
            self.metadir,
            metadata_filename
        )

        if self.uploader.check_file_exists(metadata_path):
            if self.uploader.check_file_exists(metadata_entry.r1_local):
                return

        _, barcode = self.processed.get_run_barcode(
            metadata_entry.fastq1, self.metadir)

        sample_id = self.processed.get_sample_id_from_merged(
            metadata_entry.fastq1
        )

        self.uploader.register_sample(
            metadata_entry.r1_local,
            metadata_path,
            sample_id=sample_id,
            barcode=barcode,
        )

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

    def insaflu_process_file(self, fastq_file, merged_file):
        """
        process file for televir, upload and submit"""

        new_entry = self.write_metadata(
            fastq_file, self.fastq_dir, merged_file)

        self.upload_sample(new_entry)
        self.submit_sample(new_entry)

    def insaflu_process(self):
        """
        prepare processed files for upload
        """

        files_to_upload = self.processed.processed.fastq.tolist()

        for ix, row in self.processed.processed.iterrows():

            fastq_file = row.fastq
            merged_file = row.merged
            merged_name = self.get_filename_from_path(merged_file)

            status = self.uploader.get_sample_status(merged_name)

            if self.run_metadata.upload_strategy.is_to_upload(files_to_upload, ix):

                metadata_entry = self.processed.generate_metadata_entry(
                    fastq_file, self.fastq_dir, merged_file
                )

                self.register_sample(metadata_entry)

                if status in [
                    InsafluSampleCodes.STATUS_MISSING,
                    InsafluSampleCodes.STATUS_ERROR,
                ]:

                    self.insaflu_process_file(
                        fastq_file, merged_file
                    )

    def process_folder(self):
        """
        process folder, merge and update metadata
        submit to televir only the last file.
        """
        super().process_folder()
        self.insaflu_process()


class InsafluPreMain(PreMain):
    """
    InsafluUpload class
    """

    processed: InfluProcessed
    run_metadata: InfluConfig
    projects_results: list = []

    def __init__(self, fastq_dir: str, run_metadata: InfluConfig, sleep_time: int):
        super().__init__(fastq_dir, run_metadata, sleep_time)

        self.processed = InfluProcessed(
            self.run_metadata.metadata_dir,
        )

        self.uploader = run_metadata.uploader

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.run_metadata = run_metadata

    def update_projects(self, project_file: str):
        """
        update project added
        """
        if project_file not in self.projects_results:
            if os.path.exists(project_file):
                self.projects_results.append(project_file)

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

    def monitor_samples_status(self):
        """
        process samples
        """

        fastq_list = self.uploader.logger.generate_fastq_list()
        print(len(fastq_list))

        for fastq in fastq_list:

            file_name, _ = self.processed.get_run_info(fastq.file_path)

            _ = self.uploader.update_sample_status_remote(
                file_name, fastq.file_path)

    def deploy_televir_sample(self, sample_id, file_name, file_path, project_name):
        """
        deploy televir sample
        """

        status = self.uploader.get_sample_status(
            file_name)

        if status == InsafluSampleCodes.STATUS_UPLOADED:

            status = self.uploader.deploy_televir_sample(
                sample_id,
                file_name,
                file_path,
                project_name,
            )

    def deploy_televir_batch(self):
        """
        deploy televir batch
        """
        fastq_list = self.uploader.logger.generate_fastq_list()

        for fastq in fastq_list:
            project_name = fastq.sample_id

            file_name, _ = self.processed.get_run_info(fastq.file_path)

            self.deploy_televir_sample(
                fastq.sample_id,
                file_name,
                fastq.file_path,
                project_name,
            )

    def download_project_results(self):
        """
        download project results
        """

        for sample_id in self.uploader.logger.available_samples:

            if InsafluSampleCodes.STATUS_SUBMITTED in self.uploader.logger.get_sample_status_set(sample_id):

                project_file = os.path.join(
                    self.run_metadata.metadata_dir,
                    sample_id + ".tsv"
                )

                self.uploader.get_project_results(
                    sample_id, project_file
                )

                self.update_projects(project_file)

    def run(self):
        super().run()
        print("Monitoring samples status")
        self.monitor_samples_status()
        self.export_global_metadata()

        if self.run_metadata.deploy_televir:
            print("Deploying televir batch")

            self.deploy_televir_batch()
            self.download_project_results()
            _ = plot_project_results(
                self.projects_results, self.processed.processed, self.run_metadata.output_dir)

    def run_return_plot(self):
        super().run()
        self.monitor_samples_status()
        self.export_global_metadata()

        if self.run_metadata.deploy_televir:

            self.deploy_televir_batch()
            self.download_project_results()
            return plot_project_results(
                self.projects_results, self.processed.processed, self.run_metadata.output_dir, write_html=False)

        return None
