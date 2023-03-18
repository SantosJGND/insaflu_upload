import argparse

from mfmc.mfmc import PreMain, RunConfig


def get_arguments():
    parser = argparse.ArgumentParser(description="Process fastq files.")
    parser.add_argument(
        "-i", "--in_dir", help="Input directory", required=True)
    parser.add_argument("-o", "--out_dir",
                        help="Output directory", required=True)

    parser.add_argument("-s", "--sleep", help="Sleep time",
                        required=True, type=int)

    return parser.parse_args()


def main():

    args = get_arguments()

    run_metadata = RunConfig(
        args.out_dir,

    )

    compressor = PreMain(
        args.in_dir,
        run_metadata,
        args.sleep
    )

    compressor.run_until_killed()


if __name__ == "__main__":
    main()
