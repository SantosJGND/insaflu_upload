import os
from dataclasses import dataclass

import pandas as pd

from insaflu_upload.upload_utils import InsafluUpload
from mfmc.records import Processed, RunConfig


@dataclass
class InfluConfig(RunConfig):
    """
    TelevirConfig class
    """

    uploader: InsafluUpload
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

        return new_entry.export_as_dataframe()

    def generate_metadata_entry(self, fastq_file: str, fastq_dir: str, merged_file: str):

        proj_name, barcode = self.get_run_barcode(
            merged_file, fastq_dir)

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


class MetadataEntry():
    """
    MetadataEntry class
    """

    sample_name: str
    fastq1: str
    fastq2: str
    data_set: str
    vaccine_status: str
    week: str
    onset_date: str
    collection_date: str
    lab_reception_date: str
    latitude: str
    longitude: str
    region: str
    country: str
    division: str
    location: str
    time_elapsed: str
    dir: str
    r1_local: str
    r2_local: str

    def __init__(self, sample_name: str, fastq1: str, fastq2: str = "", data_set: str = "", vaccine_status: str = "", week: str = "", onset_date: str = "", collection_date: str = "", lab_reception_date: str = "",
                 latitude: str = "", longitude: str = "", region: str = "", country: str = "", division: str = "", location: str = "", time_elapsed: int = 0, dir: str = ""):
        self.sample_name = sample_name
        self.fastq1 = os.path.basename(fastq1)
        self.fastq2 = os.path.basename(fastq2)
        self.data_set = data_set
        self.vaccine_status = vaccine_status
        self.week = week
        self.onset_date = onset_date
        self.collection_date = collection_date
        self.lab_reception_date = lab_reception_date
        self.latitude = latitude
        self.longitude = longitude
        self.region = region
        self.country = country
        self.division = division
        self.location = location
        self.time_elapsed = time_elapsed
        self.dir = dir
        self.r1_local = fastq1
        self.r2_local = fastq2

    def export_as_dataframe(self):

        metad = pd.DataFrame([self.__dict__])

        metad = metad.rename(columns={
            "sample_name": "sample name",
            "vaccine_status": "vaccine status",
            "onset_date": "onset date",
            "collection_date": "collection date",
            "data_set": "data set",
            "lab_reception_date": "lab reception date",
        })

        return metad
