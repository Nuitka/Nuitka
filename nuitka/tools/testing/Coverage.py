#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Coverage operations for Nuitka testing.

Nuitka test runs use the 'coverage' module to record which code is executed,
both for compiling with coverage and for running optimization tests. This
module wraps the invocations, and publishes the collected data.
"""

import contextlib
import os
import sys

from nuitka.Tracing import tools_logger
from nuitka.utils.Execution import check_output
from nuitka.utils.FileOperations import (
    copyFile,
    doesFileStartWithBytes,
    getFileContents,
    getPathWithForwardSlashes,
    openTextFile,
    putTextFileContents,
    withDirectoryChange,
)
from nuitka.utils.Utils import getArchitecture, getOS


def getCoverageFile():
    """Return the filename of the default coverage data file.

    Returns:
        str: Path to the '.coverage' data file in the checkout.
    """

    return os.path.join(os.path.dirname(__file__), "..", "..", "..", ".coverage")


def getCoverageRunCommand(command):
    """Wrap a Python command to run it under coverage.

    Args:
        command: Command sequence with the Python binary as first item.

    Returns:
        list: Command with the coverage invocation inserted after the Python
        binary.

    Notes:
        Using '--rcfile' avoids user configuration, and '--append' accumulates
        data from multiple test runs. The '-S' option avoids site imports,
        which would otherwise be measured as well.
    """

    # spell-checker: ignore rcfile

    return (
        list(command[0:1])
        + ["-S", "-m", "coverage", "run", "--rcfile", os.devnull, "-a"]
        + list(command[1:])
    )


def isSQLiteDatabase(filename):
    """Check if a file is a SQLite3 database.

    Args:
        filename: Filename to check.

    Returns:
        bool: True if the file starts with the SQLite3 header.
    """

    return doesFileStartWithBytes(filename, b"SQLite format 3\x00")


def makeSQLiteCoverageRelative(filename, abs_source_dir):
    """Make paths in SQLite coverage data relative to a source directory.

    Args:
        filename: Filename of the coverage data file.
        abs_source_dir: Absolute directory to strip from the recorded paths.

    Notes:
        Since coverage.py 5.0, the data file is a SQLite database, with the
        file paths stored in the 'file' table. Replacing them as text would
        corrupt the database, and decoding it as text fails.
    """

    # Local import, as this is only needed for SQLite coverage data.
    import sqlite3

    source_dir_prefix = abs_source_dir + os.path.sep

    with contextlib.closing(sqlite3.connect(filename)) as connection:
        file_rows = connection.execute("SELECT id, path FROM file").fetchall()

        for file_id, path in file_rows:
            if path.startswith(source_dir_prefix):
                path = path[len(source_dir_prefix) :]

                path = getPathWithForwardSlashes(path)

                connection.execute(
                    "UPDATE file SET path = ? WHERE id = ?", (path, file_id)
                )

        connection.commit()


def _copyToGlobalCoverageData(coverage_dir, source, target):
    """Copy coverage data to the global coverage directory.

    Args:
        coverage_dir: Directory to copy the coverage data to.
        source: Filename of the coverage data.
        target: Filename to use in the coverage directory.
    """
    copyFile(source, os.path.join(coverage_dir, target))


def publishCoverageData():
    """Publish coverage data of a test run, if configured to do so."""
    coverage_dir = os.getenv("COVERAGE_DIR")

    if coverage_dir is None:
        tools_logger.warning("No COVERAGE_DIR set, coverage data is not published.")

    suffix = getOS() + "." + getArchitecture()

    with openTextFile("data.coverage", "w") as data_file:
        # Keep publishing the testing directory as before, when this code was
        # part of the test runner package.
        source_dir = os.path.abspath(os.path.dirname(__file__))

        with withDirectoryChange(source_dir):
            nuitka_id = check_output("git rev-parse HEAD".split())
        nuitka_id = nuitka_id.strip()

        if sys.version_info > (3,):
            nuitka_id = nuitka_id.decode()

        data_file.write("NUITKA_SOURCE_DIR='%s'\n" % source_dir)
        data_file.write("NUITKA_COMMIT='%s'\n" % nuitka_id)

    if coverage_dir is not None:
        _copyToGlobalCoverageData(
            coverage_dir, "data.coverage", "meta.coverage." + suffix
        )

    def makeCoverageRelative(filename):
        """Normalize coverage data."""

        abs_source_dir = os.path.abspath(".")

        # Coverage 5.0 changed to SQLite data files, old versions that are
        # still used by Python 2.6, 3.2, 3.3, and 3.4 use JSON text files.
        if isSQLiteDatabase(filename):
            makeSQLiteCoverageRelative(filename, abs_source_dir)
            return

        data = getFileContents(filename)

        data = data.replace((abs_source_dir + os.path.sep).replace("\\", "\\\\"), "")

        if os.path.sep != "/":
            data = data.replace(os.path.sep, "/")

        putTextFileContents(filename, contents=data)

    coverage_file = os.getenv("COVERAGE_FILE", getCoverageFile())

    makeCoverageRelative(coverage_file)

    if coverage_dir is not None:
        _copyToGlobalCoverageData(
            coverage_dir, coverage_file, "data.coverage." + suffix
        )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
