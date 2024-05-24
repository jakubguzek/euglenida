import argparse
import pathlib
from logging import Logger
from typing import List, Optional, Union

from euglenida import utils


def qiime_classify(
    qiime_path: str,
    classifier_path: Union[pathlib.Path, str],
    reads_path: Union[pathlib.Path, str],
    output_path: Union[pathlib.Path, str],
) -> List[str]:
    return [
        qiime_path,
        "feature-classifier",
        "classify-sklearn",
        "--i-classifier",
        f"{classifier_path}",
        "--i-reads",
        f"{reads_path}",
        "--o-classification",
        f"{output_path}",
    ]


def qiime_metadata_tabulate(
    qiime_path: str,
    classification_path: Union[pathlib.Path, str],
    classification_visualization_path: Union[pathlib.Path, str],
) -> List[str]:
    return [
        qiime_path,
        "metadata",
        "tabulate",
        "--m-input-file",
        f"{classification_path}",
        "--o-visualization",
        f"{classification_visualization_path}",
    ]


def qiime_taxa_barplot(
    qiime_path: str,
    table_path: Union[pathlib.Path, str],
    classification_path: Union[pathlib.Path, str],
    output_barplot_path: Union[pathlib.Path, str],
    metadata_file: Optional[Union[pathlib.Path, str]] = None,
) -> List[str]:
    if metadata_file is not None:
        return [
            qiime_path,
            "taxa",
            "barplot",
            "--0-table",
            f"{table_path}",
            "--i-taxonomy",
            f"{classification_path}",
            "--m-metadata-file",
            f"{metadata_file}",
            "--o-visualization",
            f"{output_barplot_path}",
        ]
    return [
        qiime_path,
        "taxa",
        "barplot",
        "--0-table",
        f"{table_path}",
        "--i-taxonomy",
        f"{classification_path}",
        "--o-visualization",
        f"{output_barplot_path}",
    ]


def qiime_alignment_mafft(
    qiime_path: str,
    input_sequences_path: Union[pathlib.Path, str],
    output_alignment_path: Union[pathlib.Path, str],
) -> List[str]:
    return [
        qiime_path,
        "alignment",
        "mafft",
        f"{input_sequences_path}",
        "sekwencje_euglenin.qza",
        "--o-alignment",
        f"{output_alignment_path}",
    ]


def qiime_alignment_mask(
    qiime_path: str,
    input_alignment_path: Union[pathlib.Path, str],
    output_trimmed_alignment_path: Union[pathlib.Path, str],
) -> List[str]:
    return [
        qiime_path,
        "alignment",
        "mask",
        "--i-alignment",
        f"{input_alignment_path}",
        "--o-masked-alignment",
        f"{output_trimmed_alignment_path}",
    ]


def qiime_phylogeny_fasttree(
    qiime_path: str,
    input_alignment_path: Union[pathlib.Path, str],
    output_tree_path: Union[pathlib.Path, str],
) -> List[str]:
    return [
        qiime_path,
        "phylogeny",
        "fasttree",
        "--i-alignment",
        f"{input_alignment_path}",
        "--o-tree",
        f"{output_tree_path}",
    ]


def qiime_phylogeny_midpoint_root(
    qiime_path: str,
    input_tree_path: Union[pathlib.Path, str],
    output_rooted_tree_path: Union[pathlib.Path, str],
) -> List[str]:
    return [
        qiime_path,
        "phylogeny",
        "midpoint-root",
        "--i-tree",
        f"{input_tree_path}",
        "--o-rooted-tree",
        f"{output_rooted_tree_path}",
    ]


def classify(args: argparse.Namespace, logger: Logger, script_name: str) -> int:
    if args.verbose:
        utils.print_args(args, script_name=script_name)

    if args.qiime_path is None:
        print(
            f"\033[31m\033[1m{script_name}: error:\033[0m: could not find qiime2 executable in $PATH"  # ]]]
        )
        return 1

    classifier = pathlib.Path(args.classifier)
    logger.debug(f"Validating classifier file path: {classifier}")
    if not classifier.exists():
        print(
            f"\033[31m\033[1m{script_name}: error:\033[0m: {classifier}: No such file or directory!"  # ]]]
        )
        return 1

    reads_path = pathlib.Path(args.input_sequences)
    logger.debug(f"Validating reads file path: {reads_path}")
    if not reads_path.exists():
        print(
            f"\033[31m\033[1m{script_name}: error:\033[0m: {reads_path}: No such file or directory!"  # ]]]
        )
        return 1

    table_path = pathlib.Path(args.input_table)
    logger.debug(f"Validating table file path: {table_path}")
    if not table_path.exists():
        print(
            f"\033[31m\033[1m{script_name}: error:\033[0m: {table_path}: No such file or directory!"  # ]]]
        )
        return 1

    # Validate outdir path. If it doesn't exist, create it.
    output_dir: pathlib.Path = pathlib.Path(args.outdir)
    logger.debug(f"Checking if output directory ({output_dir}) exists.")
    if not output_dir.exists():
        logger.info(f"Output directory: {output_dir}, doesn't exist; creating it.")
        output_dir.mkdir()

    # Handle the changing of qiime2 tmp directory. If not done can sometimes lead
    # to errors during runnign qiime2 commands
    logger.debug(f"Setting new tmpdir.")
    tmp_dir = pathlib.Path(args.tmp_dir)
    if not tmp_dir.exists():
        tmp_dir.mkdir()
    utils.change_tmp_dir(tmp_dir, logger)

    classification_path = output_dir / "classification.qza"
    classification_command = qiime_classify(
        args.qiime_path, classifier, reads_path, classification_path
    )
    logger.info(f"Running command: {utils.command_to_str(classification_command)}")
    utils.run_command_with_output(classification_command, args, script_name, logger)

    classification_metadata_path = classification_path.with_suffix(".qzv")
    metadata_tabulate_command = qiime_metadata_tabulate(
        args.qiime, classification_path, classification_metadata_path
    )
    logger.info(f"Running command: {utils.command_to_str(metadata_tabulate_command)}")
    utils.run_command_with_output(metadata_tabulate_command, args, script_name, logger)

    barplot_output_path = output_dir / "barplot.qzv"

    logger.debug("Checking if metadata file was passed in.")
    if args.metadata is not None:
        metadata = pathlib.Path(args.metadata)
        logger.debug("Checking if passed in metadata file exists.")
        if not metadata.exists() and args.verbose:
            print(
                f"\033[31m\033[1m{script_name}: error:\033[0m: {table_path}: No such file or directory!"  # ]]]
            )
            return 1
        taxa_barplot_command = qiime_taxa_barplot(
            args.qiime_path,
            table_path,
            classification_path,
            barplot_output_path,
            metadata,
        )
    else:
        taxa_barplot_command = qiime_taxa_barplot(
            args.qiime_path, table_path, classification_path, barplot_output_path
        )

    logger.info(f"Running command: {utils.command_to_str(taxa_barplot_command)}")
    utils.run_command_with_output(taxa_barplot_command, args, script_name, logger)

    return 0


def rooted_tree(args: argparse.Namespace, logger: Logger, script_name: str):
    if args.verbose:
        utils.print_args(args, script_name=script_name)

    if args.qiime_path is None:
        print(
            f"\033[31m\033[1m{script_name}: error:\033[0m: could not find qiime2 executable in $PATH"  # ]]]
        )
        return 1

    reads_path = pathlib.Path(args.input_sequences)
    logger.debug(f"Validating reads file path: {reads_path}")
    if not reads_path.exists():
        print(
            f"\033[31m\033[1m{script_name}: error:\033[0m: {reads_path}: No such file or directory!"  # ]]]
        )
        return 1

    # Validate outdir path. If it doesn't exist, create it.
    output_dir: pathlib.Path = pathlib.Path(args.outdir)
    logger.debug(f"Checking if output directory ({output_dir}) exists.")
    if not output_dir.exists():
        logger.info(f"Output directory: {output_dir}, doesn't exist; creating it.")
        output_dir.mkdir()

    # Handle the changing of qiime2 tmp directory. If not done can sometimes lead
    # to errors during runnign qiime2 commands
    logger.debug(f"Setting new tmpdir.")
    tmp_dir = pathlib.Path(args.tmp_dir)
    if not tmp_dir.exists():
        tmp_dir.mkdir()
    utils.change_tmp_dir(tmp_dir, logger)

    alignment_output_path = output_dir / "alignment.qza"
    trimmed_alignment_path = output_dir / "alignment_trimmed.qza"
    tree_path = output_dir / "tree.qza"
    rooted_tree_path = output_dir / "rooted_tree.qza"

    alignment_command = qiime_alignment_mafft(
        args.qiime_path, reads_path, alignment_output_path
    )
    trimmed_alignment_command = qiime_alignment_mask(
        args.qiime_path, alignment_output_path, trimmed_alignment_path
    )
    tree_command = qiime_phylogeny_fasttree(
        args.qiime_path, trimmed_alignment_path, tree_path
    )
    root_command = qiime_phylogeny_midpoint_root(
        args.qiime_path, tree_path, rooted_tree_path
    )

    logger.info(f"Running command: {utils.command_to_str(alignment_command)}")
    utils.run_command_with_output(alignment_command, args, script_name, logger)
    logger.info(f"Running command: {utils.command_to_str(trimmed_alignment_command)}")
    utils.run_command_with_output(trimmed_alignment_command, args, script_name, logger)
    logger.info(f"Running command: {utils.command_to_str(tree_command)}")
    utils.run_command_with_output(tree_command, args, script_name, logger)
    logger.info(f"Running command: {utils.command_to_str(root_command)}")
    utils.run_command_with_output(root_command, args, script_name, logger)

    return 0
