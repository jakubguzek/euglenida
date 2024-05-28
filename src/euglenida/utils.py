import argparse
import os 
import subprocess 
import pathlib
from logging import Logger
from typing import Any, List


def command_to_str(command: List[Any]) -> str:
    return ' '.join([str(item) for item in command])


def new_tmp_dir_env(new_path: pathlib.Path, logger: Logger) -> dict[str, str]:
    logger.debug(f"Creating envrionment with $TMPDIR={new_path.resolve()}")
    current_env = os.environ.copy()
    current_env["TMPDIR"] = f"'{new_path.resolve()}'"
    logger.debug("Current shell envrionment:")
    logger.debug(f"{current_env}")
    return current_env


def print_args(args: argparse.Namespace, script_name) -> None:
    print(f"{script_name}: passed arguemnts:")
    for arg, value in args._get_kwargs():
        if isinstance(value, list) and len(value) > 5:
            print(f"\t{arg:<16}: [{' '.join(value[:2] +  ['...'] +value[-2:])}]")
        else:
            print(f"\t{arg:<16}: {value}")


def run_command_with_output(
    command: List[str], env: dict[str, str], args: argparse.Namespace, script_name: str, logger: Logger
):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env
    )
    try:
        for line in process.stdout:  # type: ignore
            if args.verbose or args.debug:
                print(line.decode().strip(), flush=True)
    except subprocess.SubprocessError as e:
        if args.verbose or args.debug:
            raise e
        else:
            print(
                f"\033[31m\033[1m{script_name}: error:\033[0m: critical error occured while running {command[0]}."  # ]]]
            )
            return 1
