# -*- coding: utf-8 -*-
"""Setup file for the avaframe package.

important commands:
python setup.py sdist
python setup.py build_ext --inplace
python setup.py bdist_wheel
twine uploade dist/*

To create a release (with github):
- update the version number below
- push to github
- create a release there
- run releaseWithMany.. in the actions tab

"""

# from setuptools import setup, find_packages  # Always prefer setuptools
from setuptools import Extension, setup, find_packages
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

DISTNAME = "debrisframe"
LICENSE = "EUPL"
AUTHOR = "DebrisFrame Contributors"
AUTHOR_EMAIL = "felix@avaframe.org"
URL = "http://debrisframe.org"
CLASSIFIERS = [
    # How mature is this project? Common values are
    # 3 - Alpha  4 - Beta  5 - Production/Stable
    "Development Status :: 5 - Production/Stable",
    # Indicate who your project is intended for
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: European Union Public Licence 1.2 (EUPL 1.2)",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

DESCRIPTION = "The Open Debris flow Framework"

req_packages = ["avaframe"]


# read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    # Project info
    name=DISTNAME,
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    # version=getVersion(),
    # The project's main homepage.
    url=URL,
    # Author details
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    # License
    license=LICENSE,
    classifiers=CLASSIFIERS,
    # We are a python 3 only shop
    python_requires=">=3.7",
    # Find packages automatically
    packages=find_packages(exclude=["docs"]),
    # Include package data
    include_package_data=True,
    # Install dependencies
    install_requires=req_packages,
    # additional groups of dependencies here (e.g. development dependencies).
    extras_require={},
    # Run build_ext
    # options=setup_options,
    # Executable scripts
    entry_points={},
    zip_safe=False,
    # ext_modules=extensions,
)
