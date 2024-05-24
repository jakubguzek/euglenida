#!/usr/bin/env python
# MIT License
#
# Copyright (c) 2023 Jakub J. Guzek
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import functools
import itertools
import pathlib
import re
import sys
from enum import Enum
from typing import Callable, List, Optional, TypeVar, Type, Iterable

# Keep script name in global constant
SCRIPT_NAME = pathlib.Path(__file__).name
# Type vairable for type annotation in ManifestFile class.
S = TypeVar("S", bound="ManifestFile")


# Custom Error
class InferenceError(ValueError):
    """Raised whene direction of reads cannot be inferred."""

    ...


class Direction(Enum):
    """Represents direction of reads."""

    Forward = "forward"
    Reverse = "reverse"
    Unknown = "Unknown"


class ManifestFile:
    """Represents manifest file."""

    HEADER = "sample-id,absolute-filepath,direction\n"

    def __init__(self, filepath: pathlib.Path) -> None:
        self._path: pathlib.Path = filepath
        self.name: str = self._path.name
        self.exists = self._path.exists()
        # Lines represent entries in manifest file.
        # Lines that should already be in file.
        self._lines: List[str] = []
        # Lines that have not been written to the file yet.
        self._unwritten_lines = [self.HEADER]

    @classmethod
    def from_file(cls: Type[S], filepath: pathlib.Path) -> S:
        """Returns a ManifestFile class instance from path to existing manifest file."""
        lines: List[str] = []
        with open(filepath, "r") as file:
            for line in file.readlines():
                lines.append(line)
        # Create a new ManifestFile instance
        new = cls(filepath)
        # Overwrite ._lines attribute with lines read from existing manifest file.
        new._lines = lines
        # Remove header from list of unwritten lines.
        new._unwritten_lines = []
        return new

    @property
    def lines(self) -> List[str]:
        """List of lines that should've already been written to the file"""
        return self._lines

    @property
    def unwritten_lines(self) -> List[str]:
        """List of lines that were not yet written to the file."""
        return self._unwritten_lines

    def add_file(self, name: str, file_path: str, direction: Direction) -> None:
        """Adds new file entry (row) to the manifest file list of unwritten lines."""
        self._unwritten_lines.append(f"{name},{file_path},{direction.value}\n")

    def extend_manifest(
        self,
        files: Iterable[pathlib.Path],
        infer: bool,
        substitution_function: Optional[Callable]= None
    ) -> None:
        """Adds entries to the ManifestFile for all files in files Iterable."""
        for file in files:
            direction = Direction.Unknown
            filename = file.stem
            if infer:
                direction = infer_direction(file)
            if substitution_function is not None:
                filename = substitution_function(string=filename)
            self.add_file(filename, f"{file.absolute()}", direction)

    def emit(self, mode: str) -> None:
        """Creates new manifest file or appends to manifest file  on the filesystem."""
        with open(self._path, mode) as file:
            for line in self._unwritten_lines:
                file.write(line)
        # Move unwritten lines to self._lines and then remove the
        # contents of self._unwritten_lines
        self._lines.extend(self.unwritten_lines)
        self._unwritten_lines.clear()


def parse_args() -> argparse.Namespace:
    """Returns parsed command-line arguments of the script."""
    description = (
        "simple command-line utility for generating meanifest files for qiime2. "
        "Sample names (sample-id column) are generated automatically and "
        "\033[1musually require correction.\033[0m " #]]
        "By default header and generated entries will be returned to stdout. Options "
        "-o and -a are provided to output generated entries to files. Option -i can "
        "be used to get automatic inference of reads' direction. however it's not "
        "guaranteed to work everytime. By default direction in generated manifest "
        "needs to be edited manually. "
        "For now this utility works only with uncompressed fasta files."
    )
    parser = argparse.ArgumentParser(description=description)
    output = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "files", type=str, nargs="+", metavar="file", help="file(s) to add to manifest"
    )
    output.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="write generated manifest rows to FILE",
    )
    output.add_argument(
        "-a",
        "--append",
        type=str,
        metavar="FILE",
        help="append generated manifest rows to FILE",
    )
    parser.add_argument(
        "-i",
        "--infer",
        action="store_true",
        help="infer the direction from sequence identifier. Works only for standard Illumina identifiers",
    )
    parser.add_argument(
        "-n",
        "--no-overwrite",
        action="store_true",
        help="don't overwrite existing files when creating manifest (rquires -o option)",
    )
    parser.add_argument(
        "-r",
        "--regex-pattern",
        type=str,
        help="Regular expression that will be matched against file names to create sample names",
    )
    return parser.parse_args()


# raises InferenceError
def infer_direction(filepath: pathlib.Path, n=100) -> Direction:
    """Returns a direction of reads in a file given by a filepath.

    It is assumed here that all reads in a file are same members of their pairs, i.e.
    All are either forward or reverse. This function checks first n lines for a file
    in seach of sequence identifier from which it can infer the direction of a sequence.

    Raises: InferenceError"""

    # Anonymous functions for getting a number representing a member of a pair
    # of paired end reads (1 or 2). It is assumed here that first member (1) is
    # always in forward direction and second (2) member is always in reverse.
    old_format = lambda x: x.split(":")[4][-1]  # pre-Casava 1.8
    new_format = lambda x: x.split(" ")[1].split(":")[0]  # post-Casava 1.8
    member_number: int = 0
    with open(filepath, "r") as file:
        # Create an iterator containing only first n lines of a file.
        lines = itertools.islice(file, n)
        for line in lines:
            # Check only identifier lines.
            if line.startswith("@"):
                try:
                    member_number = new_format(line)
                except IndexError:
                    member_number = old_format(line)
                except (IndexError, TypeError):
                    # Raise inference error if wasn't able to infer.
                    raise InferenceError(
                        f"{SCRIPT_NAME}: error: couldn't infer direction in file: {filepath.name}"
                    )
                break
    if member_number == "1":
        return Direction.Forward
    elif member_number == "2":
        return Direction.Reverse
    else:
        # Return Unknown if for some reason member_number was not 1 or 2 after parsing.
        return Direction.Unknown


def main() -> int:
    args = parse_args()
    # Get paths to files as pathlb.Path objects. Makes working with paths later, easier.
    files = [pathlib.Path(file) for file in args.files]

    # if any of the files is not a fastq file print an error message and return 1,
    # meaning a failure
    if not all(".fastq" == file.suffix for file in files):
        print(
            f"{SCRIPT_NAME}: error: All files must be valid fastq files and their names must end with '.fastq'"
        )
        return 1
    if not all(file.exists() for file in files):
        print(
            f"{SCRIPT_NAME}: error: [Errno 2] No such file or directory '{next(filter(lambda x: not x.exists(), files))}'"
        )
        return 2

    # Instantiate ManifestFile accordingly to passed command-line arguments.
    if args.append:
        file = pathlib.Path(args.append)
        if not file.exists():
            print(f"{SCRIPT_NAME}: error: File {file} not found!")
            return 1
        manifest = ManifestFile.from_file(pathlib.Path(args.append))
    elif args.output:
        file = pathlib.Path(args.output)
        if args.no_overwrite:
            if file.exists():
                print(f"{SCRIPT_NAME}: error: File {file} exists!")
                return 1
        manifest = ManifestFile(pathlib.Path(args.output))
    else:
        manifest = ManifestFile(pathlib.Path("stdout"))

    # Add entries to ManifestFile
    if args.regex_pattern:
        try:
            _, pattern, repl, options = re.split(r'(?<![^\\]\\)/', args.regex_pattern)
        except ValueError:
            print(
                f"{SCRIPT_NAME}: error: substitution string must be sed-like, that is of a form: `s/pattern/replacement/[g]`."
            )
            return 1
        else:
            replace_function = functools.partial(
                re.sub, pattern=pattern, repl=re.sub(r'\\/', '/', repl), count = "g" not in options
            )
            manifest.extend_manifest(files, args.infer, replace_function)
    else:
        manifest.extend_manifest(files, args.infer)

    # Create manifest file or append to existing manifest file. Else print
    # results to stdout. Return 0, meaning a success.
    if args.append:
        manifest.emit("a")
    elif args.output:
        manifest.emit("w")
    else:
        for line in manifest.unwritten_lines:
            print(line, end="")
    return 0


# Run main if script was called directly and not imported by other python module
if __name__ == "__main__":
    sys.exit(main())
