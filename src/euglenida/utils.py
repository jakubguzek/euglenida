import argparse
import os
import subprocess
import pathlib
import sys
from typing import List


def change_tmp_dir(new_path: pathlib.Path) -> None:
    os.environ["TMPDIR"] = f"'{new_path.resolve()}'"


def print_args(args: argparse.Namespace, script_name) -> None:
    print(f"{script_name}: passed arguemnts:")
    for arg, value in args._get_kwargs():
        if isinstance(value, list) and len(value) > 5:
            print(f"\t{arg:<16}: [{' '.join(value[:2] +  ['...'] +value[-2:])}]")
        else:
            print(f"\t{arg:<16}: {value}")


def run_command_with_output(
    command: List[str], args: argparse.Namespace, script_name: str
):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
    )
    try:
        for c in iter(lambda: process.stdout.read(1), b""):  # type: ignore
            sys.stdout.buffer.write(c)
    except subprocess.SubprocessError as e:
        if args.verbose:
            raise e
        else:
            print(
                f"\033[31m\033[1m{script_name}: error:\033[0m: critical error occured while running {command[0]}."  # ]]]
            )
            return 1
