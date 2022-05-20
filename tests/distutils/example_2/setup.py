#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Example setup file to test Nuitka distutils integration.

"""

from setuptools import find_packages, setup

# use `python setup.py bdist_nuitka` to use nuitka or use
# in the setup(..., build_with_nuitka=True, ...)
# and bdist and build will allways use nuitka

setup(
    name="bdist_nuitka_test_2",
    description="nuitka bdist_nuitka test-case compiling interdependent"
    + " python packages, and printing a data file",
    author="Nobody really",
    author_email="email@someplace.com",
    version="0.8.2",
    py_modules=[],
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    command_options={
        "nuitka": {
            "--show-scons": ("setup.py", True),
            "--show-progress": None,
            "--file-reference-choice": "original",
        }
    },
    package_data={"": ["*.txt"]},
    entry_points={"console_scripts": ["runner = package1.main:main"]},
    zip_safe=False,
)
