import argparse
import itertools
import pathlib
from logging import Logger
from typing import List, Tuple, Union

import joblib

from euglenida import utils


def qiime_tools_import(
    qiime_path: str,
    input_path: Union[pathlib.Path, str],
    output_path: Union[pathlib.Path, str],
) -> List[str]:
    return [
        qiime_path,
        "tools",
        "import",
        "--type",
        "SampleData[PairedEndSequencesWithQuality]",
        "--input-format",
        "PairedEndFastqManifestPhred33",
        "--input-path",
        f"{input_path}",
        "--output-path",
        f"{output_path}",
    ]


def qiime_demux_summarize(
    qiime_path: str,
    imported_reads_filepath: Union[pathlib.Path, str],
    output_visualization_path: Union[pathlib.Path, str],
) -> List[str]:
    return [
        qiime_path,
        "demux",
        "summarize",
        "--i-data",
        f"{imported_reads_filepath}",
        "--o-visualization",
        f"{output_visualization_path}",
    ]


def qiime_dada2(
    qiime_path: str,
    imported_reads_filepath: Union[pathlib.Path, str],
    stats_output_filename: Union[pathlib.Path, str],
    filtered_sequences_filename: Union[pathlib.Path, str],
    summary_table_filename: Union[pathlib.Path, str],
    truncate_forward_at: int,
    truncate_reverse_at: int,
    trim_forward_by: int,
    trim_reverse_by: int,
    truncate_threshold_quality: int,
    verbose: bool,
    chimera_method: str = "consensus",
) -> List[str]:
    command = [
        qiime_path,
        "dada2",
        "denoise-paired",
        "--i-demultiplexed-seqs",
        f"{imported_reads_filepath}",
        "--p-trunc-len-f",
        f"{truncate_forward_at}",
        "--p-trunc-len-r",
        f"{truncate_reverse_at}",
        "--p-trim-left-f",
        f"{trim_forward_by}",
        "--p-trim-left-r",
        f"{trim_reverse_by}",
        "--p-chimera-method",
        f"{chimera_method}",
        "--p-trunc-q",
        f"{truncate_threshold_quality}",
        "--o-denoising-stats",
        f"{stats_output_filename}",
        "--o-representative-sequences",
        f"{filtered_sequences_filename}",
        "--o-table",
        f"{summary_table_filename}",
    ]
    if verbose:
        command.append("--verbose")
    return command


def qiime_metadata_tabulate(
    qiime_path: str,
    input_stats_filename: Union[pathlib.Path, str],
    output_stats_filename: Union[pathlib.Path, str],
) -> List[str]:
    return [
        qiime_path,
        "metadata",
        "tabulate",
        "--m-input-file",
        f"{input_stats_filename}",
        "--o-visualization",
        f"{output_stats_filename}",
    ]


def qiime_feature_table_summarize(
    qiime_path: str,
    input_table: Union[pathlib.Path, str],
    output_table: Union[pathlib.Path, str],
) -> List[str]:
    return [
        qiime_path,
        "feature-table",
        "summarize",
        "--i-table",
        f"{input_table}",
        "--o-visualization",
        f"{output_table}",
    ]


def qiime_tools_export(
    qiime_path: str,
    input_path: Union[pathlib.Path, str],
    output_dir: Union[pathlib.Path, str],
) -> List[str]:
    return [
        qiime_path,
        "tools",
        "export",
        "--input-path",
        f"{input_path}",
        "--output-path",
        f"{output_dir}",
    ]


def preprocess(args: argparse.Namespace, logger: Logger, script_name: str) -> int:
    if args.verbose or args.debug:
        utils.print_args(args, script_name=script_name)

    if args.qiime_path is None:
        print(
            f"\033[31m\033[1m{script_name}: error:\033[0m: could not find qiime2 executable in $PATH"  # ]]]
        )
        return 1

    manifest = pathlib.Path(args.qiime2_manifest)
    if not manifest.exists():
        print(
            f"\033[31m\033[1m{script_name}: error:\033[0m: {manifest}: No such file or directory!"  # ]]]
        )
        return 1

    # Validate outdir path. If it doesn't exist, create it.
    output_dir: pathlib.Path = pathlib.Path(args.outdir)
    logger.debug(f"Checking if output directory ({output_dir}) exists.")
    if not output_dir.exists():
        logger.info(f"Output directory: {output_dir}, doesn't exist; creating it.")
        output_dir.mkdir()

    imported_reads_artifact_path = output_dir / "reads.qza"

    logger.debug("Setting trimming parameters.")
    trimming_parameters: list[tuple[int, ...]] = list(
        itertools.product(
            args.trunc_len_f,
            args.trunc_len_r,
            args.trim_left_f,
            args.trim_left_r,
            args.trunc_q,
        )
    )

    # Handle the changing of qiime2 tmp directory. If not done can sometimes lead
    # to errors during runnign qiime2 commands
    logger.debug(f"Setting new tmpdir.")
    tmp_dir = pathlib.Path(args.tmp_dir)
    if not tmp_dir.exists():
        tmp_dir.mkdir()
    env_with_tmpdir = utils.new_tmp_dir_env(tmp_dir, logger)

    import_command = qiime_tools_import(
        args.qiime_path, manifest, imported_reads_artifact_path
    )
    demux_summarization_command = qiime_demux_summarize(
        args.qiime_path,
        imported_reads_artifact_path,
        imported_reads_artifact_path.with_suffix(".qzv"),
    )

    logger.info(f"Running command: `{utils.command_to_str(import_command)}`")
    utils.run_command_with_output(
        import_command, env_with_tmpdir, args, script_name, logger
    )
    logger.info(
        f"Running command: `{utils.command_to_str(demux_summarization_command)}`"
    )
    utils.run_command_with_output(
        demux_summarization_command, env_with_tmpdir, args, script_name, logger
    )

    def filter_and_merge(
        trunc_f: int, trunc_r: int, trim_f: int, trim_r: int, trunc_q: int
    ):
        filtering_stats_path = (
            output_dir
            / f"filtering_stats_{trunc_f}_{trunc_r}_{trim_f}_{trim_r}_{trunc_q}.qza"
        )
        logger.debug(f"filtering stats path: {filtering_stats_path}")

        filtered_sequences_path = (
            output_dir
            / f"filtered_reads_{trunc_f}_{trunc_r}_{trim_f}_{trim_r}_{trunc_q}.qza"
        )
        logger.debug(f"filtered sequences path: {filtering_stats_path}")

        filtering_table_path = (
            output_dir
            / f"filtering_table_{trunc_f}_{trunc_r}_{trim_f}_{trim_r}_{trunc_q}.qza"
        )
        logger.debug(f"filtering table path: {filtering_stats_path}")

        dada2_command = qiime_dada2(
            args.qiime_path,
            imported_reads_artifact_path,
            filtering_stats_path,
            filtered_sequences_path,
            filtering_table_path,
            truncate_forward_at=trunc_f,
            truncate_reverse_at=trunc_r,
            trim_forward_by=trim_f,
            trim_reverse_by=trim_r,
            truncate_threshold_quality=trunc_q,
            verbose=args.verbose,
        )

        logger.info(f"Running command: {utils.command_to_str(dada2_command)}")
        utils.run_command_with_output(
            dada2_command, env_with_tmpdir, args, script_name, logger
        )

        filtering_stats_command = qiime_metadata_tabulate(
            args.qiime_path,
            filtering_stats_path,
            filtering_stats_path.with_suffix(".qzv"),
        )
        table_visualiztion_command = qiime_feature_table_summarize(
            args.qiime_path,
            filtering_table_path,
            filtering_table_path.with_suffix(".qzv"),
        )

        logger.info(f"Running command: {utils.command_to_str(filtering_stats_command)}")
        utils.run_command_with_output(
            filtering_stats_command, env_with_tmpdir, args, script_name, logger
        )
        logger.info(
            f"Running command: {utils.command_to_str(table_visualiztion_command)}"
        )
        utils.run_command_with_output(
            table_visualiztion_command, env_with_tmpdir, args, script_name, logger
        )

        filtering_table_dir = output_dir / filtering_table_path.stem
        logger.debug(f"Creating filtering table output dir: {filtering_table_dir}")
        filtering_table_dir.mkdir()

        table_export_command = qiime_tools_export(
            args.qiime_path, filtering_table_path, filtering_table_dir
        )

        filtered_sequences_dir = output_dir / filtered_sequences_path.stem
        logger.debug(
            f"Creating filtered sequences output dir: {filtered_sequences_dir}"
        )
        filtered_sequences_dir.mkdir()

        sequences_export_command = qiime_tools_export(
            args.qiime_path, filtered_sequences_path, filtered_sequences_dir
        )

        logger.info(f"Running command: {utils.command_to_str(table_export_command)}")
        utils.run_command_with_output(
            table_export_command, env_with_tmpdir, args, script_name, logger
        )
        logger.info(
            f"Running command: {utils.command_to_str(sequences_export_command)}"
        )
        utils.run_command_with_output(
            sequences_export_command, env_with_tmpdir, args, script_name, logger
        )

    logger.info(
        f"Combinations of trimming and quality-based truncation parameters: {trimming_parameters}"
    )
    logger.info(
        f"Running filtering and merging for different combinations of parameters."
    )
    # joblib.Parallel(n_jobs=args.threads)(
    #     joblib.delayed(filter_and_merge)(trunc_f, trunc_r, trim_f, trim_r, trunc_q)
    #     for trunc_f, trunc_r, trim_f, trim_r, trunc_q in trimming_parameters
    # )
    for trunc_f, trunc_r, trim_f, trim_r, trunc_q in trimming_parameters:
        filter_and_merge(trunc_f, trunc_r, trim_f, trim_r, trunc_q)

    return 0
