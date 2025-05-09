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

setup(
    # Find packages automatically
    packages=find_packages(exclude=["docs"]),
    # Include package data
    include_package_data=True,
    # Run build_ext
    # options=setup_options,
    # Executable scripts
    entry_points={},
    zip_safe=False,
    # ext_modules=extensions,
)
