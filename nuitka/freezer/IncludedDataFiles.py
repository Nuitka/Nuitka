#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Included data files for standalone mode.

This keeps track of data files for standalone mode. Do not should them for
DLLs or extension modules, these need to be seen by Nuitka as entry points
for dependency analysis.
"""

import collections

IncludedDataFile = collections.namedtuple(
    "IncludedDataFile", ("kind", "source_path", "dest_path", "reason")
)


def makeIncludedEmptyDirectories(source_path, dest_paths, reason):
    return IncludedDataFile(
        kind="empty_dirs", source_path=source_path, dest_path=dest_paths, reason=reason
    )


def makeIncludedDataFile(source_path, dest_path, reason):
    return IncludedDataFile(
        kind="datafile", source_path=source_path, dest_path=dest_path, reason=reason
    )
