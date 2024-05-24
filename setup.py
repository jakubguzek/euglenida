#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import io
import os.path
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ) as fh:
        return fh.read()


setup(
    name="euglenida",
    version="0.2.0",
    license="MIT",
    description="Scripts and programs for metagenomics project analyses",
    long_description="{}".format(
        re.compile("^.. start-badges.*^.. end-badges", re.M | re.S).sub(
            "", read("README.md")
        )
    ),
    long_description_content_type="text/markdown",
    author="Jakub J. Guzek",
    author_email="jj.guzek@student.uw.edu.pl",
    url="file://" + os.path.abspath(dirname(__file__)),
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Topic :: Utilities",
        "Typing :: Typed",
        "Private :: Do Not Upload",
    ],
    keywords=[
        # eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    python_requires=">=3.9",
    install_requires=[
        "joblib>=1.4"
    ],
    entry_points={
        "console_scripts": [
            "euglenins = euglenida:euglenins.py",
        ]
    },
)
