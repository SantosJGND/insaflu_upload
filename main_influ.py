
import argparse

from insaflu_upload.insaflu_upload import InfluConfig, InsafluUpload


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
    parser.add_argument("-s", "--sleep", help="Sleep time", default=5,
                        type=int)

    return parser.parse_args()


def main():

    args = get_arguments()

    run_metadata = InfluConfig(
        args.out_dir,
        args.tsv_t_n,
        args.tsv_t_dir,
    )

    compressor = InsafluUpload(
        args.in_dir,
        run_metadata,
        args.sleep
    )

    compressor.run_until_killed()


if __name__ == "__main__":
    main()
