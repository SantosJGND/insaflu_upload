
import datetime
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Type

import pandas as pd

from insaflu_upload.plot_utils import plot_project_results
from insaflu_upload.records import InsafluFile, MetadataEntry
from insaflu_upload.tables_post import InsafluTables
from insaflu_upload.upload_utils import (InsafluSampleCodes, InsafluUpload,
                                         UploadStrategy)
from mfmc.mfmc import DirectoryProcessingSimple, PreMain
from mfmc.records import ProcessAction, Processed


@dataclass
class InfluConfig:
    """
    TelevirConfig class
    """
    output_dir: str
    name_tag: str
    uploader: InsafluUpload
    upload_strategy: Type[UploadStrategy]
    actions: Optional[List[Type[ProcessAction]]] = None
    tsv_temp_name: str = "televir_metadata.tsv"
    metadata_dirname: str = "metadata_dir"
    logs_dirname: str = "logs"
    keep_name: bool = False
    deploy_televir: bool = False
    db_path: str = "insaflu.db"

    def __post_init__(self):
        self.output_dir = os.path.abspath(self.output_dir)
        self.name_tag = self.name_tag.strip()
        self.uploader = self.uploader
        self.upload_strategy = self.upload_strategy
        self.actions = self.actions
        self.tsv_temp_name = self.tsv_temp_name.strip()

        self.keep_name = self.keep_name
        self.deploy_televir = self.deploy_televir

        self.metadata_dir = os.path.join(
            self.output_dir, self.metadata_dirname)

        self.logs_dir = os.path.join(self.output_dir, self.logs_dirname)
        self.db_path = os.path.join(self.logs_dir, self.db_path)

        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        self.tables = InsafluTables(self.db_path)
        self.tables.setup()


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

        return new_entry.export_as_dataframe()

    def generate_metadata_entry(self, fastq_file: str, fastq_dir: str, merged_file: str, tag=""):

        sample_name, _ = self.get_run_barcode(
            merged_file, fastq_dir)

        time_elapsed = self.get_file_time(
            fastq_file=fastq_file,
            fastq_dir=fastq_dir
        )
        new_entry = MetadataEntry(
            sample_name=sample_name,
            fastq1=merged_file,
            time_elapsed=float(time_elapsed),
            fdir=os.path.dirname(merged_file),
            tag=tag
        )

        return new_entry

    def generate_metadata(self):
        """
        create tsv
        """
        metadata = pd.DataFrame()

        for index, row in self.processed.iterrows():
            metadata = pd.concat(
                [metadata, self.generate_metadata_entry_row(row)])

        return metadata

    def export_metadata(self, run_metadata: InfluConfig):
        """
        export metadata
        """
        influ_metadata = self.generate_metadata()

        influ_metadata.to_csv(
            os.path.join(
                run_metadata.metadata_dir,
                run_metadata.tsv_temp_name
            ),
            sep="\t",
            index=False,
        )


class InfluDirectoryProcessing(DirectoryProcessingSimple):
    """
    TelevirDirectoryProcessing class
    replace directory gen to include metadata
    """

    metadata_suffix: str = "_metadata.tsv"

    uploader: InsafluUpload

    def __init__(self, fastq_dir: str, run_metadata: InfluConfig, processed: InfluProcessed,
                 start_time: float):
        super().__init__(fastq_dir, run_metadata, processed, start_time)

        self.run_metadata = run_metadata
        self.processed = processed
        self.uploader = run_metadata.uploader

        # self.metadir = os.path.join(
        #    self.run_metadata.metadata_dir,
        #    os.path.basename(fastq_dir.strip("/")),
        #    self.metadata_dirname,
        # )

    def prep_output_dirs(self):
        """create output dirs"""

        for outdir in [
            self.merged_gz_dir,
            # self.metadir,
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

    def register_sample(self, metadata_entry: MetadataEntry):
        """
        register sample to remote server"""

        if self.uploader.check_file_exists(metadata_entry.r1_local):
            return

        _, barcode = self.processed.get_run_barcode(
            metadata_entry.fastq1, self.fastq_dir)

        sample_id = self.processed.get_sample_id_from_merged(
            metadata_entry.fastq1
        )

        self.uploader.register_sample(
            metadata_entry.r1_local,
            sample_id=sample_id,
            barcode=barcode,
        )

    def upload_sample(self, metadata_entry: MetadataEntry):
        """
        upload sample to remote server"""

        _, barcode = self.processed.get_run_barcode(
            metadata_entry.fastq1, self.fastq_dir)

        sample_id = self.processed.get_sample_id_from_merged(
            metadata_entry.fastq1
        )

        self.uploader.upload_sample(
            metadata_entry.r1_local,
            sample_id=sample_id,
            barcode=barcode,
        )

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
                    fastq_file, self.fastq_dir, merged_file, tag=self.run_metadata.name_tag
                )

                self.register_sample(metadata_entry)

                if status in [
                    InsafluSampleCodes.STATUS_MISSING,
                    InsafluSampleCodes.STATUS_ERROR,
                ]:

                    self.upload_sample(
                        metadata_entry
                    )

    def process_folder(self):
        """
        process folder, merge and update metadata
        submit to televir only the last file.
        """
        super().process_folder()
        self.insaflu_process()


class InsafluFileProcess(PreMain):
    """
    InsafluUpload class
    """

    processed: InfluProcessed
    run_metadata: InfluConfig
    projects_results: list = []
    metadata_dirname = "metadata_dir"

    def __init__(self, fastq_dir: str, run_metadata: InfluConfig, sleep_time: int):
        super().__init__(fastq_dir, run_metadata, sleep_time)

        self.processed = InfluProcessed(
            self.run_metadata.metadata_dir,
        )

        self.uploader = run_metadata.uploader

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.run_metadata = run_metadata
        self.prep_metadata_dir()

    def prep_metadata_dir(self):
        """
        create output directories
        """

        os.makedirs(self.run_metadata.metadata_dir, exist_ok=True)

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

    def write_metadata(self, metadata: List[MetadataEntry], metadata_filename: str):
        """
        update metadata
        """

        metadata_df = [
            x.export_as_dataframe() for x in metadata
        ]

        metadata_df = pd.concat(metadata_df)

        metadata_df.to_csv(
            metadata_filename,
            sep="\t",
            index=False,
        )

    def metadata_from_files(self, files_list: List[InsafluFile]) -> List[MetadataEntry]:
        """
        generate metadata from files
        """
        metadata_list = [
            self.processed.generate_metadata_entry(
                x.file_path,
                self.fastq_dir,
                x.remote_path,
                tag=self.run_metadata.name_tag
            ) for x in files_list
        ]
        return metadata_list

    def get_samples_to_submit(self) -> List[InsafluFile]:
        """
        get samples to submit
        """
        samples_to_submit = self.uploader.logger.generate_fastq_list()

        samples_to_submit = [
            x for x in samples_to_submit if x.status == InsafluSampleCodes.STATUS_UPLOADED]

        return samples_to_submit

    def generate_metatadata_filename(self):
        """
        generate metadata filename
        """
        time_now = datetime.datetime.now()
        formatted_time = time_now.strftime("%Y%m%d_%H%M%S")

        metadata_filename = f"{self.run_metadata.name_tag}_{formatted_time}_metadata.tsv"
        return metadata_filename

    def submit(self):
        """
        submit sample to remote server"""

        samples_to_submit = self.get_samples_to_submit()
        sample_metadata = self.metadata_from_files(samples_to_submit)

        if len(sample_metadata) == 0:
            return

        print(f"Submitting {len(sample_metadata)} samples")

        self.submit_samples(sample_metadata)

    def submit_samples(self, sample_metadata: List[MetadataEntry]):
        """
        submit samples
        """
        insaflu_metadata_file = self.generate_metatadata_filename()
        metadata_filepath = os.path.join(
            self.run_metadata.metadata_dir,
            insaflu_metadata_file
        )

        self.write_metadata(
            sample_metadata,
            metadata_filepath
        )

        self.uploader.upload_file(
            metadata_filepath,
            self.uploader.get_remote_path(insaflu_metadata_file),
            "metad",
            "metad",
            self.uploader.TAG_METADATA,
        )

        status = self.uploader.logger.get_file_status(metadata_filepath)

        if status == InsafluSampleCodes.STATUS_UPLOADED:

            self.uploader.submit_sample(
                insaflu_metadata_file,
            )

    def export_global_metadata(self):

        self.prep_metadata_dir()
        self.processed.export_metadata(
            self.run_metadata
        )

    def save_to_db(self):
        """
        save to db
        """
        self.uploader.logger.save_entries_to_db(
            self.run_metadata.tables.insaflu_files)

    def monitor_samples_status(self):
        """
        process samples
        """

        fastq_list = self.uploader.logger.generate_fastq_list()

        for fastq in fastq_list:

            file_name, _ = self.processed.get_run_info(fastq.file_path)

            _ = self.uploader.update_sample_status_remote(
                file_name, fastq.file_path)

    def run(self):
        super().run()
        print("Monitoring samples status")
        self.submit()
        self.monitor_samples_status()
        self.export_global_metadata()
        self.save_to_db()


class TelevirFileProcess(PreMain):
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

        if self.run_metadata.deploy_televir:
            print("Deploying televir batch")

            self.deploy_televir_batch()
            self.download_project_results()
            # _ = plot_project_results(
            #    self.projects_results, self.processed.processed, self.run_metadata.output_dir)

    def run_return_plot(self):

        if self.run_metadata.deploy_televir:

            self.deploy_televir_batch()
            self.download_project_results()
            return plot_project_results(
                self.projects_results, self.processed.processed, self.run_metadata.output_dir, write_html=False)

        return None
