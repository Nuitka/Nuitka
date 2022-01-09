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
import os

from nuitka.utils.FileOperations import isRelativePath

IncludedDataFile = collections.namedtuple(
    "IncludedDataFile", ("kind", "source_path", "dest_path", "reason", "data")
)


def makeIncludedEmptyDirectories(source_path, dest_paths, reason):
    for dest_path in dest_paths:
        assert not os.path.isabs(dest_path)

    # Require that to not be empty.
    assert dest_paths

    return IncludedDataFile(
        kind="empty_dirs",
        source_path=source_path,
        dest_path=dest_paths,
        data=None,
        reason=reason,
    )


def makeIncludedDataFile(source_path, dest_path, reason):
    assert isRelativePath(dest_path), dest_path

    return IncludedDataFile(
        kind="data_file",
        source_path=source_path,
        dest_path=dest_path,
        data=None,
        reason=reason,
    )


IncludedDataDirectory = collections.namedtuple(
    "IncludedDataDirectory",
    (
        "kind",
        "source_path",
        "dest_path",
        "reason",
        "ignore_dirs",
        "ignore_filenames",
        "ignore_suffixes",
        "only_suffixes",
        "normalize",
    ),
)


def makeIncludedDataDirectory(
    source_path,
    dest_path,
    reason,
    ignore_dirs=(),
    ignore_filenames=(),
    ignore_suffixes=(),
    only_suffixes=(),
    normalize=True,
):
    assert isRelativePath(dest_path), dest_path

    return IncludedDataDirectory(
        kind="data_dir",
        source_path=source_path,
        dest_path=dest_path,
        ignore_dirs=ignore_dirs,
        ignore_filenames=ignore_filenames,
        ignore_suffixes=ignore_suffixes,
        only_suffixes=only_suffixes,
        normalize=normalize,
        reason=reason,
    )


def makeIncludedGeneratedDataFile(data, dest_path, reason):
    assert isRelativePath(dest_path), dest_path

    return IncludedDataFile(
        kind="data_blob",
        source_path=None,
        dest_path=dest_path,
        reason=reason,
        data=data,
    )
