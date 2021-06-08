#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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

from setuptools import setup

# use `python setup.py bdist_nuitka` to use nuitka or use
# in the setup(..., build_with_nuitka=True, ...)
# and bdist and build will allways use nuitka

setup(
    name='bdist_nuitka_test_3',
    description='nuitka bdist_nuitka test-case compiling a namespace package',
    author='Some Three',
    author_email = "email@someplace.com",
    version="0.2",
    packages=["outer.inner"],
    entry_points={
        'console_scripts': [
            'runner = outer.inner.main:main'
        ]
    },

)
