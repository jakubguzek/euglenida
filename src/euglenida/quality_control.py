import argparse
import pathlib

from euglenida import utils


def quality_control(args: argparse.Namespace, script_name) -> int:
    if args.verbose:
        utils.print_args(args, script_name=script_name)

    # Validate input file paths
    input_files = [pathlib.Path(path) for path in args.input_files]
    files_exist = [path.exists() for path in input_files]
    if not all(files_exist):
        non_existent_file = input_files[files_exist.index(False)]
        print(
            f"\033[31m\033[1m{script_name}: error:\033[0m: {non_existent_file}: No such file or directory!"  # ]]]
        )
        return 1

    # Validate outdir path. If it doesn't exist, create it.
    output_dir: pathlib.Path = pathlib.Path(args.outdir)
    if not output_dir.exists():
        output_dir.mkdir()

    # Create fastqc file if it doesn't exist.
    fastqc_dir: pathlib.Path = output_dir / args.fastqc_dirname
    if not fastqc_dir.exists():
        fastqc_dir.mkdir()

    # Create multiqc file if it doesn't exist.
    multiqc_dir: pathlib.Path = output_dir / args.multiqc_dirname
    if not multiqc_dir.exists():
        multiqc_dir.mkdir()

    fastqc_command = [
        f"{args.fastqc_path}",
        "--nogroup",
        "--threads",
        f"{args.threads}",
        *input_files,
        "--outdir",
        f"{fastqc_dir}",
    ]
    utils.run_command_with_output(fastqc_command, args, script_name)

    multiqc_command = [
        f"{args.multiqc_path}",
        "--interactive",
        "--export",
        f"{fastqc_dir}",
        "--outdir",
        f"{multiqc_dir}",
    ]
    utils.run_command_with_output(multiqc_command, args, script_name)

    return 0
