
import argparse

from insaflu_upload.connectors import ConnectorDocker, ConnectorParamiko
from insaflu_upload.insaflu_upload import InfluConfig, InsafluPreMain
from insaflu_upload.records import UploadAll, UploadLast
from insaflu_upload.upload_utils import InsafluUploadRemote
from mfmc.records import ProcessActionMergeWithLast


def get_arguments():

    parser = argparse.ArgumentParser(description="Process fastq files.")
    parser.add_argument(
        "-i", "--in_dir", help="Input directory", required=True)
    parser.add_argument("-o", "--out_dir",
                        help="Output directory", required=True)
    parser.add_argument("-t", "--tsv_t_n",
                        help="TSV template name", default="templates_comb.tsv")
    parser.add_argument("-d", "--tsv_t_dir",
                        help="TSV template directory", required=True)
    parser.add_argument("-s", "--sleep", help="Sleep time", default=60,
                        type=int)

    parser.add_argument("-n", "--tag", help="name tag, if given, will be added to the output file names",
                        required=False, type=str, default="")

    parser.add_argument("--config", help="config file",
                        required=False, type=str, default="config.ini")

    parser.add_argument("--merge", help="merge files", action="store_true")

    parser.add_argument('--upload',
                        default='last',
                        choices=['last', 'all'],
                        help='file upload stategy (default: all)',)

    parser.add_argument('--connect',
                        default='docker',
                        choices=['docker', 'ssh'],
                        help='file upload stategy (default: all)',)

    parser.add_argument(
        "--keep_names", help="keep original file names", action="store_true")

    return parser.parse_args()


def main():

    args = get_arguments()

    # create connector

    if args.connect == 'docker':
        connector = ConnectorDocker(args.config)

    else:
        connector = ConnectorParamiko(args.config)

    insaflu_upload = InsafluUploadRemote(connector, args.config)

    # determine upload strategy
    if args.upload == 'last':
        upload_strategy = UploadLast
    else:
        upload_strategy = UploadAll

    # determine actions
    actions = []
    if args.merge:
        actions.append(ProcessActionMergeWithLast)

    # create run metadata

    run_metadata = InfluConfig(
        output_dir=args.out_dir,
        name_tag=args.tag,
        uploader=insaflu_upload,
        upload_strategy=upload_strategy,
        actions=actions,
        tsv_temp_name=args.tsv_t_n,
        metadata_dir=args.tsv_t_dir,
        keep_name=args.keep_names
    )

    # run

    compressor = InsafluPreMain(
        args.in_dir,
        run_metadata,
        args.sleep
    )

    compressor.run_until_killed()


if __name__ == "__main__":
    main()
