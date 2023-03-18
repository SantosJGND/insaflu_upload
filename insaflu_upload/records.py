import pandas as pd


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

    def __init__(self, sample_name: str, fastq1: str, fastq2: str = "", data_set: str = "", vaccine_status: str = "", week: str = "", onset_date: str = "", collection_date: str = "", lab_reception_date: str = "",
                 latitude: str = "", longitude: str = "", region: str = "", country: str = "", division: str = "", location: str = "", time_elapsed: int = 0, dir: str = ""):
        self.sample_name = sample_name
        self.fastq1 = fastq1
        self.fastq2 = fastq2
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
