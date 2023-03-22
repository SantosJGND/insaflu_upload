import configparser
import os
import sys
from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd
import paramiko


class Connector(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def test_connection(self):
        pass

    @abstractmethod
    def execute_command(self, command: str) -> str:
        pass

    @abstractmethod
    def check_file_exists(self, file_path: str) -> bool:
        pass

    @abstractmethod
    def upload_file(self, file_path: str, remote_path: str):
        pass

    @abstractmethod
    def download_file(self, file_path: str, remote_path: str):
        pass

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ConnectorParamiko(Connector):

    def __init__(self, config_file: str) -> None:
        super().__init__()
        self.prep_input(config_file)
        self.connect()

    def input_config(self, config_file: str):

        config = configparser.ConfigParser()
        config.read(config_file)

        username = config["SSH"].get("username", None)
        ip_address = config["SSH"].get("ip_address", None)
        rsa_key_path = config["SSH"].get("rsa_key", None)

        if username is None or ip_address is None or rsa_key_path is None:
            raise ValueError("Config file is missing values")

        return username, ip_address, rsa_key_path

    def input_user(self):
        username = input("username: ")
        ip_address = input("ip_address: ")
        rsa_key_path = input("rsa_key (full path): ")

        return username, ip_address, rsa_key_path

    def prep_input(self, config_file: Optional[str] = None):
        if config_file is None:
            username, ip_address, rsa_key_path = self.input_user()
        try:
            username, ip_address, rsa_key_path = self.input_config(config_file)
        except FileNotFoundError:
            print("Config file not found, please input manually")
            username, ip_address, rsa_key_path = self.input_user()

        self.username = username
        self.ip_address = ip_address
        self.rsa_key_path = rsa_key_path

    def connect(self):

        paramiko_rsa_key = paramiko.RSAKey.from_private_key_file(
            self.rsa_key_path)
        self.rsa_key = paramiko_rsa_key

        self.conn = paramiko.SSHClient()
        self.conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.test_connection()

    def __enter__(self):

        self.conn.connect(
            hostname=f"{self.ip_address}",
            username=f"{self.username}",
            pkey=self.rsa_key
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def test_connection(self) -> None:
        """
        test using paramiko using rsa key. If successful, close connection, else exit
        """

        try:
            self.conn.connect(
                hostname=f"{self.ip_address}",
                username=f"{self.username}",
                pkey=self.rsa_key
            )
            self.conn.close()
        except Exception:
            print("Authentication failed, please verify your credentials")
            sys.exit(1)

    def execute_command(self, command: str) -> str:
        """
        execute command using paramiko"""

        with self as conn:
            stdin, stdout, stderr = self.conn.exec_command(command)

            return stdout.read().decode("utf-8")

    def check_file_exists(self, file_path: str) -> bool:
        """
        check file exists using paramiko"""

        with self as conn:
            stdin, stdout, stderr = self.conn.exec_command(f"ls {file_path}")

            if len(stdout.read().decode("utf-8")) > 0:
                if "cannot access" in stdout.read().decode("utf-8"):
                    return False

                return True

            return False

    def upload_file(self, file_path: str, remote_path: str):
        """
        upload file using paramiko"""
        with self as conn:
            ftp_client = self.conn.open_sftp()
            ftp_client.put(file_path, remote_path)
            ftp_client.close()

    def download_file(self, remote_path: str, file_path: str):
        """
        download file using paramiko"""
        with self as conn:
            ftp_client = self.conn.open_sftp()
            ftp_client.get(remote_path, file_path)
            ftp_client.close()


class InsafluSampleCodes:
    STATUS_MISSING = 0
    STATUS_UPLOADING = 1
    STATUS_UPLOADED = 2
    STATUS_SUBMITTED = 3
    STATUS_PROCESSING = 4
    STATUS_PROCESSED = 5
    STATUS_SUBMISSION_ERROR = 6
    STATUS_ERROR = 7


class UploadLog:

    STATUS_MISSING = InsafluSampleCodes.STATUS_MISSING
    STATUS_UPLOADING = InsafluSampleCodes.STATUS_UPLOADING
    STATUS_UPLOADED = InsafluSampleCodes.STATUS_UPLOADED
    STATUS_SUBMITTED = InsafluSampleCodes.STATUS_SUBMITTED
    STATUS_PROCESSING = InsafluSampleCodes.STATUS_PROCESSING
    STATUS_PROCESSED = InsafluSampleCodes.STATUS_PROCESSED
    STATUS_SUBMISSION_ERROR = InsafluSampleCodes.STATUS_SUBMISSION_ERROR
    STATUS_ERROR = InsafluSampleCodes.STATUS_ERROR

    columns = [
        "barcode",
        "file_path",
        "remote_path",
        "status"
    ]

    def __init__(self) -> None:
        self.log = pd.DataFrame(
            columns=[
                "barcode",
                "file_path",
                "remote_path",
                "status"
            ]
        )

    def check_entry_exists(self, file_path: str) -> bool:
        """
        check entry exists"""

        return file_path in self.log["file_path"].values

    def modify_entry(self, file_path: str, status: int) -> None:
        """
        modify entry"""

        self.log.loc[self.log["file_path"] == file_path, "status"] = status

    def update_log(self, sample_id: str, file_path: str, remote_path: str, status: int):
        """
        update upload log"""

        if self.check_entry_exists(file_path):
            self.modify_entry(file_path, status)
        else:
            self.new_entry(sample_id, file_path, remote_path)

    def new_entry(self, barcode: str, file_path: str, remote_path: str, status: int = STATUS_UPLOADED, tag: Optional[str] = None) -> None:
        """
        new entry"""

        self.log = pd.concat(
            [
                self.log,
                pd.DataFrame(
                    {
                        "barcode": [barcode],
                        "file_path": [file_path],
                        "remote_path": [remote_path],
                        "status": [status],
                        "tag": tag
                    }
                )
            ]
        )

    def get_log(self) -> pd.DataFrame:
        return self.log

    def get_file_status(self, file_path: str) -> int:
        """
        get file status"""

        return self.log.loc[self.log["file_path"] == file_path, "status"].values[0]


class InsafluUpload(ABC):

    """
    requires:
    metadata data frame with merged file path.
    copy method. (copy, move)
    user name.
    """

    logger: UploadLog
    remote_dir: str = "/usr/local/web_site/INSaFLU/media/uploads/"
    app_dir = "/usr/local/web_site/INSaFLU/"

    @abstractmethod
    def prep_upload(self):
        """
        prepare upload"""
        pass

    @abstractmethod
    def test_connection(self):
        """
        test connection"""
        pass

    @abstractmethod
    def get_remote_path(self, file_path):
        """
        get remote path"""
        pass

    @abstractmethod
    def check_file_exists(self, file_path):
        """
        check file exists"""
        pass

    @abstractmethod
    def upload_file(self, file_path, remote_path, file_id: str, tag: str):
        """
        upload file"""
        pass

    @abstractmethod
    def download_file(self, remote_path, file_path):
        """
        download file"""
        pass

    @abstractmethod
    def upload_sample(self, fastq_path: str, metadata_path: str, sample_id: str):
        """
        upload sample using metadir and fastq path"""
        pass

    @abstractmethod
    def submit_sample(self, metadata_path: str):
        """
        submit sample"""
        pass

    @staticmethod
    def check_submission_success(submission_output) -> bool:
        """
        check submission success"""

        if "exists in database" in submission_output:
            return True

        elif "file was processed" in submission_output:
            return True

        return False

    @abstractmethod
    def update_log(self, sample_id: str, file_path: str, remote_path: str, status: int):
        """
        update log"""
        pass

    @staticmethod
    def translate_sample_status(status_output: str):
        """
        translate sample status"""

        if "matching query does not exist" in status_output:
            return InsafluSampleCodes.STATUS_MISSING
        elif "Is Ready" in status_output:
            if "True" in status_output:
                return InsafluSampleCodes.STATUS_UPLOADED
            else:
                return InsafluSampleCodes.STATUS_UPLOADING

        return InsafluSampleCodes.STATUS_ERROR

    @staticmethod
    def translate_televir_submission_output(submission_output):
        """
        translate televir submission output"""

        if "submitted" in submission_output:
            if "already" in submission_output:
                return InsafluSampleCodes.STATUS_SUBMITTED

            return InsafluSampleCodes.STATUS_SUBMITTED

        return InsafluSampleCodes.STATUS_SUBMISSION_ERROR

    @staticmethod
    def translate_televir_status_output(status_output):

        if "Error" in status_output:
            return InsafluSampleCodes.STATUS_ERROR

        return InsafluSampleCodes.STATUS_PROCESSING

    @abstractmethod
    def get_sample_status(self, sample_name) -> int:
        """
        get sample status"""
        pass

    @abstractmethod
    def clean_upload(self, file_path: str):
        """
        clean upload"""
        pass

    @abstractmethod
    def launch_televir_project(self, sample_name: str, project_name: Optional[str] = None):
        """
        launch televir project"""
        pass

    @abstractmethod
    def get_project_status(self, project_name: str):
        """
        get project status"""
        pass

    @abstractmethod
    def get_project_id(self, project_name: str):
        """
        get project id"""
        pass

    @abstractmethod
    def get_project_results(self, project_id: str):
        """
        get project results"""
        pass


class InsafluUploadRemote(InsafluUpload):

    # conn: Connector
    logger: UploadLog
    TAG_FASTQ = "fastq"
    TAG_METADATA = "metadata"

    def __init__(self, connector: Connector, config_file: str) -> None:
        super().__init__()
        self.logger = UploadLog()
        self.conn = connector
        self.prep_upload()
        self.prep_user(config_file=config_file)

    def input_config(self, config_file: str):

        config = configparser.ConfigParser()
        config.read(config_file)

        username = config["INSAFLU"].get("username", None)

        if username is None:
            raise ValueError("username not found in config file")

        return username

    def input_user(self):
        username = input("INSaFLU username: ")

        return username

    def prep_user(self, config_file: Optional[str] = None):

        if config_file is None:
            self.televir_user = self.input_user()
        else:
            try:
                self.televir_user = self.input_config(config_file=config_file)
            except ValueError:
                self.televir_user = self.input_user()

    def prep_upload(self):
        """
        prepare upload"""
        self.django_manager = os.path.join(
            self.app_dir,
            "manage.py"
        )

        self.test_connection()

    def test_connection(self):
        """
        test connection
        """

        self.conn.test_connection()

    def update_log(self, sample_id: str, file_path: str, remote_path: str, status: int = UploadLog.STATUS_UPLOADED):
        """
        update upload log"""

        self.logger.update_log(
            sample_id=sample_id,
            file_path=file_path,
            remote_path=remote_path,
            status=status
        )

    def get_remote_path(self, file_path):

        return os.path.join(
            self.remote_dir,
            os.path.basename(file_path)
        )

    def check_file_exists(self, file_path: str):
        """
        check file exists"""

        return self.conn.check_file_exists(file_path)

    def upload_file(self, file_path: str, remote_path: str, file_id="NA", tag: Optional[str] = None):
        """
        upload file to remote server"""

        file_name = os.path.basename(file_path)
        status = self.logger.STATUS_MISSING
        if self.conn.check_file_exists(remote_path):
            status = self.logger.STATUS_UPLOADED
            print("File already exists: ", file_path)

        else:
            try:
                self.conn.upload_file(
                    file_path,
                    remote_path)

                status = self.logger.STATUS_UPLOADED

            except Exception as error:

                print("Error uploading file: ", file_path)
                print(error)
                status = self.logger.STATUS_ERROR

        self.logger.new_entry(
            barcode=file_id,
            file_path=file_path,
            remote_path=remote_path,
            status=status,
            tag=tag
        )

    def download_file(self, remote_path: str, local_path: str):
        """
        download file from remote server"""

        if self.conn.check_file_exists(remote_path):
            try:
                self.conn.download_file(remote_path, local_path)
                print("File downloaded: ", remote_path)
            except Exception as error:
                print("Error downloading file: ", remote_path)
                print(error)

    def upload_sample(self, fastq_path: str, metadata_path: str, sample_id: str = "NA"):
        """
        upload sample using metadir and fastq path"""

        self.upload_file(
            metadata_path,
            self.get_remote_path(metadata_path),
            sample_id,
            self.TAG_METADATA
        )

        self.upload_file(
            fastq_path,
            self.get_remote_path(fastq_path),
            sample_id,
            self.TAG_FASTQ
        )

    def submit_sample(self, metadata_path: str):
        """
        submit sample"""
        remote_metadata_path = self.get_remote_path(metadata_path)

        if not self.check_file_exists(remote_metadata_path):
            print("Remote metadata file does not exist: ", remote_metadata_path)
            return

        output = self.conn.execute_command(
            f"python3 {self.django_manager} upload_samples --metadata_file {remote_metadata_path} --user_login {self.televir_user}"
        )

        success = self.check_submission_success(output)
        if success:
            print(f"Metadata submission success: ", metadata_path)
        success_tag = InsafluSampleCodes.STATUS_UPLOADED if success else InsafluSampleCodes.STATUS_SUBMISSION_ERROR

        self.update_log(
            sample_id="NA",
            file_path=metadata_path,
            remote_path=remote_metadata_path,
            status=success_tag
        )

    def get_sample_status(self, sample_name: str):
        """
        get sample status"""
        sample_status = self.conn.execute_command(
            f"python3 {self.django_manager} check_sample_status --name {sample_name} --user_login {self.televir_user}"
        )

        return self.translate_sample_status(sample_status)

    def clean_upload(self, file_path: str):
        """
        clean upload"""

        if self.check_file_exists(file_path):
            self.conn.execute_command(
                f"rm {file_path}"
            )

    def launch_televir_project(self, sample_name: str, project_name: Optional[str] = None):
        """
        launch televir project"""

        if project_name is None:
            project_name = sample_name

        command = [
            "python3",
            self.django_manager,
            "create_televir_from_sample",
            "--sample_name",
            sample_name,
            "--user_login",
            self.televir_user,
            "--project_name",
            project_name
        ]

        command = " ".join(command)

        submit_status = self.conn.execute_command(
            command
        )

        return self.translate_televir_submission_output(submit_status)

    def get_project_status(self, project_name: str):

        results = self.get_project_results(project_name)

        return self.translate_televir_status_output(results)

    def get_project_id(self):
        pass

    def get_project_results(self, project_name: str):

        command = [
            "python3",
            self.django_manager,
            "check_televir_results",
            "--user_login",
            self.televir_user,
            "--project_name",
            project_name
        ]

        command = " ".join(command)

        submit_status = self.conn.execute_command(
            command
        )

        submit_status = submit_status.splitlines()[-1]

        return submit_status
