#     Copyright 2017, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Utils for file and directory operations.

This provides enhanced and more error resilient forms of standard
stuff. It will also frequently add sorting.

"""

import os

from .Utils import joinpath


def listDir(path):
    """ Give a sorted path, base filename pairs of a directory."""

    return sorted(
        [
            (
                joinpath(path, filename),
                filename
            )
            for filename in
            os.listdir(path)
        ]
    )


def getSubDirectories(path):
    result = []

    for root, dirnames, _filenames in os.walk(path):
        for dirname in dirnames:
            result.append(
                joinpath(root, dirname)
            )

    result.sort()
    return result
