import itertools
import pathlib
import re
import sys
from typing import Collection, Optional, Sequence

import joblib
import joblib_progress
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pandas.core.generic import describe_ndframe
import seaborn as sns

SCRIPT_NAME = pathlib.Path(__file__).name

READS_DIR = pathlib.Path("./data/raw/")
FORWARD_STARTER = "CTGTGAATGGCTCCTTACATCAG"
REVERSE_STARTER = "CTSCCTCTCCGGAATCRAAC"
SPECIAL_BASES = {"R": "[AG]", "S": "[CG]"}


def count_sequences_with(pattern: re.Pattern, sequences: Collection[str]) -> int:
    n = 0
    for sequence in sequences:
        if pattern.match(sequence) is not None:
            n += 1
    return n


def prepare_regex_pattern(
    string: str, mapping: Optional[dict[str, str]] = None
) -> re.Pattern:
    if mapping is None:
        return re.compile(string)

    for k, v in mapping.items():
        string = string.replace(k, v)
    return re.compile(f"^{string}")


def count_starters_in_file(file: pathlib.Path, starter_sequence: str):
    with open(file, "r") as f:
        lines = [line.strip() for line in itertools.islice(f, 1, None, 4)]

    occurances = {}
    for i in range(13, -1, -1):
        if i > len(starter_sequence):
            i = len(starter_sequence)
        forward_starter_re = prepare_regex_pattern(starter_sequence[i:], SPECIAL_BASES)
        starter_occurances = count_sequences_with(forward_starter_re, lines)
        occurances[i] = starter_occurances

    return occurances


def calculate_starter_stats(
    input_directory: pathlib.Path,
    forward_starter: str,
    reverse_starter: str,
) -> pd.DataFrame:
    fastq_forward_files: list[pathlib.Path] = list(input_directory.glob("*1.fastq"))
    fastq_reverse_files: list[pathlib.Path] = list(input_directory.glob("*2.fastq"))

    file_starter_pairs: Sequence[tuple[pathlib.Path, str]] = [
        (file, forward_starter) for file in fastq_forward_files
    ] + [(file, reverse_starter) for file in fastq_reverse_files]

    with joblib_progress.joblib_progress(
        description="Counting starters in fastq files...", total=len(file_starter_pairs)
    ):
        starter_occurances = joblib.Parallel(n_jobs=12)(
            joblib.delayed(count_starters_in_file)(file, starter)
            for file, starter in file_starter_pairs
        )

    starter_occurances_per_file = {
        path.stem: occurances
        for (path, _), occurances in zip(file_starter_pairs, starter_occurances)
    }
    df = pd.DataFrame(starter_occurances_per_file).transpose()
    return df


def get_lengths(file_path: pathlib.Path) -> tuple[str, pd.Series]:
    with open(file_path, "r") as f:
        lengths = [len(line.strip()) for line in itertools.islice(f, 1, None, 4)]
    return file_path.stem, pd.Series(lengths)


def calculate_reads_lengths(
    input_directory: pathlib.Path,
):
    files: list[pathlib.Path] = list(input_directory.glob("*fastq"))

    with joblib_progress.joblib_progress(
        description="Calculating reads lengths in fastq files...", total=len(files)
    ):
        reads_lengths = joblib.Parallel(n_jobs=12)(
            joblib.delayed(get_lengths)(path) for path in files
        )

    if reads_lengths is not None:
        df = pd.DataFrame({name: lengths for name, lengths in reads_lengths}).melt().dropna()  # type: ignore
        df["direction"] = (
            df["variable"].str[-1].map({"1": "Forawrd", "2": "Reverse"}).tolist()
        )
        df.columns = ["Sample ID", "Read length", "Direction"]
    else:
        raise ValueError

    return df


def main() -> int:
    # df = calculate_starter_stats(READS_DIR, FORWARD_STARTER, REVERSE_STARTER)
    # df.to_csv("./data/intermediate/starter_o curances.tsv", sep="\t")

    df = calculate_reads_lengths(READS_DIR)
    print(df)
    fig, axs = plt.subplots(
        nrows=2, ncols=1, gridspec_kw={"height_ratios": [2, 1]}, sharex=True
    )
    sns.histplot(df, x="Read length", hue="Direction", ax=axs[0], bins=100)
    sns.boxplot(df, x="Read length", hue="Direction", ax=axs[1], legend=False, showfliers=False)
    plt.tight_layout()
    plt.show()

    return 0


if __name__ == "__main__":
    sys.exit(main())
