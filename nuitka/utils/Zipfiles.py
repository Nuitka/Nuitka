#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Zip file utilities."""

import contextlib
import os
import zipfile

from nuitka.PythonVersions import python_version

if python_version < 0x300:
    _BadZipFile = zipfile.BadZipfile
else:
    _BadZipFile = zipfile.BadZipFile


@contextlib.contextmanager
def getZipFile(zip_path, error_exit, logger):
    """Open a zip file as context manager, handling BadZipFile.

    Args:
        zip_path: Path to the zip file.
        error_exit: If True, BadZipFile triggers logger.sysexit, else raise.
        logger: Logger with sysexit method.

    Yields:
        ZipFile object.
    """
    try:
        zip_file = zipfile.ZipFile(zip_path, "r")
    except _BadZipFile:
        if error_exit:
            logger.sysexit("Bad zip file '%s'." % zip_path)

        raise

    try:
        yield zip_file
    finally:
        zip_file.close()


def extractZipFile(zip_path, target_dir, get_target_filename, error_exit, logger):
    """Extract selected files from a zip file.

    Args:
        zip_path: Path to the zip file.
        target_dir: Directory to extract the files into.
        get_target_filename: Callable taking a member name and returning the
            relative target filename, or 'None' to skip the member.
        error_exit: If True, BadZipFile triggers logger.sysexit, else raise.
        logger: Logger with sysexit method.
    """
    with getZipFile(
        zip_path=zip_path, error_exit=error_exit, logger=logger
    ) as zip_file:
        for zip_info in zip_file.infolist():
            target_filename = get_target_filename(zip_info.filename)

            if target_filename is None:
                continue

            original_filename = zip_info.filename
            zip_info.filename = target_filename

            try:
                zip_file.extract(zip_info, target_dir)
            finally:
                zip_info.filename = original_filename


def doesZipFileMatch(zip_path, decide_filename, error_exit, logger):
    """Check if any file in zip matches decide function.

    Args:
        zip_path: Path to the zip file.
        decide_filename: Callable taking filename, returns True if matches.
        error_exit: If True, BadZipFile triggers logger.sysexit.
        logger: Logger with sysexit method.

    Returns:
        True if any filename matches, False if not or BadZipFile and not error_exit.
    """
    if not os.path.isfile(zip_path):
        return False

    try:
        with getZipFile(
            zip_path=zip_path, error_exit=error_exit, logger=logger
        ) as zip_file:
            return any(decide_filename(filename) for filename in zip_file.namelist())
    except _BadZipFile:
        return False


def createZipFile(file_obj):
    """Create a zip file for writing with best compression.

    Args:
        file_obj: File object to write zip to.

    Returns:
        ZipFile object opened for writing.
    """
    # ZIP_LZMA is not used for 2.6 compat and Tcl decompression support.
    if python_version < 0x370:
        return zipfile.ZipFile(file_obj, "w", compression=zipfile.ZIP_DEFLATED)

    return zipfile.ZipFile(
        file_obj, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
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
