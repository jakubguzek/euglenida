#!/usr/bin/env python
import argparse
import datetime
import logging
import pathlib
import shutil
import sys
from typing import Union

from euglenida import quality_control
from euglenida import preprocessing
from euglenida import taxonomy


SCRIPT_NAME = pathlib.Path(__file__).name

DEFAULT_OUTPUT_DIR = "./results"
DEFAULT_PREPROCESSING_OUTPUT_DIR = "./results/qiime2"
DEFAULT_CLASSIFICATION_OUTPUT_DIR = "./results/classification"
DEFAULT_TMP_DIR = "./data/tmp"
DEFAULT_FASTQC_DIRNAME = "fastqc"
DEFAULT_MULTIQC_DIRNAME = "multiqc"

FASTQC_PATH = shutil.which("fastqc")
MULTIQC_PATH = shutil.which("multiqc")
QIIME2_PATH = shutil.which("qiime")

VERBOSITY = 30


# Function to setup the logger. Generated using ChatGPT, because boilerplate
# Edited by me to add some more functionality like checking if passed log_file
# path exists, passing in loggin-level and type hints..
def setup_logger(log_filepath: str, logging_level: int = VERBOSITY):
    # Create a custom logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging_level)

    log_file = pathlib.Path(log_filepath)
    if log_file.exists():
        print(
            "[\033[34m\033[1mwarning\033[0m] Passed log file already exists. "  # ]]]
            "New logging data will be appended at the end of the file."
        )

    # Create handlers
    console_handler = logging.StreamHandler()  # Console handler
    file_handler = logging.FileHandler(log_file)  # File handler

    # Set the level for handlers
    console_handler.setLevel(logging_level)
    file_handler.setLevel(logging_level)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose", action="store_true", help="make the program more verbose."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="print all debug information; not recommended.",
    )
    parser.add_argument("--log-filepath", type=str, help="where logs should be saved.")
    commands = parser.add_subparsers(title="Commands", dest="command", required=True)

    # QA
    qa_parser = commands.add_parser(
        "qc",
        help="Run quality control programs (fastqc, multiqc) and save their outputs.",
    )
    qa_parser.add_argument(
        "input_files",
        nargs="*",
        type=str,
        help="any number of fastq files on which the qc will be run.",
    )
    qa_parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        default=DEFAULT_OUTPUT_DIR,
        help=f"where to save the results. If not specified: `{DEFAULT_OUTPUT_DIR}`.",
    )
    qa_parser.add_argument(
        "--verbose", action="store_true", help="make the program more verbose."
    )
    qa_parser.add_argument(
        "--debug",
        action="store_true",
        help="print all debug information; not recommended.",
    )
    qa_parser.add_argument(
        "--fastqc-dirname",
        type=str,
        default=DEFAULT_FASTQC_DIRNAME,
        help=f"name of the directory with fastqc results that will be created in outdir. Default: `{DEFAULT_FASTQC_DIRNAME}`.",
    )
    qa_parser.add_argument(
        "--fastqc-path",
        type=str,
        default=FASTQC_PATH,
        help=f"path to fastqc executable. Default: {FASTQC_PATH}",
    )
    qa_parser.add_argument(
        "--multiqc-dirname",
        type=str,
        default=DEFAULT_MULTIQC_DIRNAME,
        help=f"name of the directory with multiqc results that will be created in outdir. Default: `{DEFAULT_MULTIQC_DIRNAME}`.",
    )
    qa_parser.add_argument(
        "--multiqc-path",
        type=str,
        default=MULTIQC_PATH,
        help=f"path to multiqc executable. Default: {MULTIQC_PATH}",
    )
    qa_parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=2,
        help="Number of threads to use for quality control programs.",
    )

    # Preprcessing of data with qiime2
    preprocessing_parser = commands.add_parser(
        "preprocess",
        aliases=["pp"],
        help=(
            "Import data into qiime2."
            "Trim, filter, merge forward and reverse reads, "
            "filter out chimeric sequences and genereate filtering "
            "results visualization qiime2 artifact"
        ),
    )
    preprocessing_parser.add_argument(
        "qiime2_manifest",
        type=str,
        help="path to qiime2 manifest csv file. Can be genereated using `generate_qiime_manifest` script.",
    )
    preprocessing_parser.add_argument(
        "--qiime-path", type=str, default=QIIME2_PATH, help="path to qiime2 executable."
    )
    preprocessing_parser.add_argument(
        "--verbose", action="store_true", help="make the program more verbose."
    )
    preprocessing_parser.add_argument(
        "--debug",
        action="store_true",
        help="print all debug information; not recommended.",
    )
    preprocessing_parser.add_argument(
        "--tmp-dir",
        type=str,
        default=DEFAULT_TMP_DIR,
        help="path to tmp directory used by qiime2.",
    )
    preprocessing_parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        default=DEFAULT_PREPROCESSING_OUTPUT_DIR,
        help=f"where to save the results. If not specified: `{DEFAULT_PREPROCESSING_OUTPUT_DIR}`.",
    )
    preprocessing_parser.add_argument(
        "--trunc-len-f",
        nargs=2,
        type=int,
        default=[200, 200],
        help="how long should the forward reads be after trimming them at the ends.",
    )
    preprocessing_parser.add_argument(
        "--trunc-len-r",
        nargs=2,
        type=int,
        default=[200, 200],
        help="how long should the reverse reads be after trimming them at the ends.",
    )
    preprocessing_parser.add_argument(
        "--trim-left-f",
        nargs=2,
        type=int,
        default=[10, 10],
        help="how many nucleotides should be trimmed from the start of forward reads",
    )
    preprocessing_parser.add_argument(
        "--trim-left-r",
        nargs=2,
        type=int,
        default=[10, 10],
        help="how many nucleotides should be trimmed from the start of reverse reads",
    )
    preprocessing_parser.add_argument(
        "--trunc-q", nargs=2, type=int, default=[15, 15], help="qulity-based truncation"
    )
    preprocessing_parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=2,
        help="Number of threads to use for quality control programs.",
    )

    # Taxonomy classification
    taxonomy_parser = commands.add_parser(
        "taxonomy",
        aliases=["classify"],
        help=("Run taxonomical classification of sequences and create visualizations"),
    )
    taxonomy_parser.add_argument(
        "classifier", type=str, help="path to classifier qiime artifact file."
    )
    taxonomy_parser.add_argument(
        "input_sequences",
        type=str,
        help="path to qiime2 artifact file with sequences to classify.",
    )
    taxonomy_parser.add_argument(
        "input_table",
        type=str,
        help="path to qiime2 artifact file with table after filtering.",
    )
    taxonomy_parser.add_argument(
        "--qiime-path", type=str, default=QIIME2_PATH, help="path to qiime2 executable."
    )
    taxonomy_parser.add_argument(
        "--verbose", action="store_true", help="make the program more verbose."
    )
    taxonomy_parser.add_argument(
        "--debug",
        action="store_true",
        help="print all debug information; not recommended.",
    )
    taxonomy_parser.add_argument(
        "--tmp-dir",
        type=str,
        default=DEFAULT_TMP_DIR,
        help="path to tmp directory used by qiime2.",
    )
    taxonomy_parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        default=DEFAULT_CLASSIFICATION_OUTPUT_DIR,
        help=f"where to save the results. If not specified: `{DEFAULT_CLASSIFICATION_OUTPUT_DIR}`.",
    )
    taxonomy_parser.add_argument(
        "-m", "--metadata", type=str, help="file with sample metadata metadata."
    )

    # Tree construction
    tree_parser = commands.add_parser(
        "tree",
        help=(
            "Construct phylogenetic tree of ASVs using fasttree algorithm implementation in qiime2."
        ),
    )
    tree_parser.add_argument(
        "input_sequences",
        type=str,
        help="path to qiime2 artifact file with sequences, for which the tree will be constructed.",
    )
    tree_parser.add_argument(
        "--qiime-path", type=str, default=QIIME2_PATH, help="path to qiime2 executable."
    )
    tree_parser.add_argument(
        "--verbose", action="store_true", help="make the program more verbose."
    )
    tree_parser.add_argument(
        "--debug",
        action="store_true",
        help="print all debug information; not recommended.",
    )
    tree_parser.add_argument(
        "--tmp-dir",
        type=str,
        default=DEFAULT_TMP_DIR,
        help="path to tmp directory used by qiime2.",
    )
    tree_parser.add_argument(
        "-o",
        "--outdir",
        type=str,
        default=DEFAULT_CLASSIFICATION_OUTPUT_DIR,
        help=f"where to save the results. If not specified: `{DEFAULT_CLASSIFICATION_OUTPUT_DIR}`.",
    )

    return parser.parse_args()


def euglenins() -> int:
    args = parse_args()

    global VERBOSITY
    if args.verbose:
        VERBOSITY = 20
    if args.debug:
        VERBOSITY = 10

    if args.log_filepath:
        log_filepath = args.log_filepath
    else:
        log_filepath = f"{__file__}_{args.command}_{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}"

    logger = setup_logger(log_filepath, logging_level=VERBOSITY)

    if args.command == "qc":
        return quality_control.quality_control(args, logger, script_name=SCRIPT_NAME)
    elif args.command == "preprocess" or args.command == "pp":
        return preprocessing.preprocess(args, logger, script_name=SCRIPT_NAME)
    elif args.command == "taxonomy" or args.command == "classify":
        return taxonomy.classify(args, logger, script_name=SCRIPT_NAME)
    elif args.command == "tree":
        return taxonomy.rooted_tree(args, logger, script_name=SCRIPT_NAME)

    return 0


if __name__ == "__main__":
    sys.exit(euglenins())
