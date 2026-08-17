#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Interface to data composer"""

import os
import subprocess
import sys

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.options.Options import shallUseDirectConstantBlobs
from nuitka.plugins.Hooks import onDataComposerResult, onDataComposerRun
from nuitka.PythonVersions import isRunningInInterpreter
from nuitka.States import states
from nuitka.Tracing import data_composer_logger
from nuitka.utils.CStrings import encodePythonIdentifierToC
from nuitka.utils.Execution import withEnvironmentVarsOverridden
from nuitka.utils.FileOperations import (
    changeFilenameExtension,
    getFileSize,
    getNormalizedPathJoin,
    makeContainingPath,
    makePath,
)
from nuitka.utils.Json import loadJsonFromFilename

# Indicate not done with -1
_data_composer_size = None
_data_composer_stats = None
_constant_blob_symbol_bases = {}
_constant_blob_symbol_origins = {}


def getDataComposerReportValues():
    return OrderedDict(blob_size=_data_composer_size, stats=_data_composer_stats)


def runDataComposer(source_dir):
    # This module is a singleton, pylint: disable=global-statement
    global _data_composer_stats

    onDataComposerRun()
    blob_filenames, _data_composer_stats = _runDataComposer(source_dir=source_dir)
    onDataComposerResult(blob_filenames)

    global _data_composer_size
    _data_composer_size = sum(
        getFileSize(blob_filename) for blob_filename in blob_filenames
    )


def _runDataComposer(source_dir):
    data_composer_path = os.path.normpath(
        getNormalizedPathJoin(os.path.dirname(__file__), "..", "tools", "data_composer")
    )

    mapping = {
        "NUITKA_PACKAGE_HOME": os.path.dirname(
            os.path.abspath(sys.modules["nuitka"].__path__[0])
        )
    }

    if states.data_composer_verbose:
        mapping["NUITKA_DATA_COMPOSER_VERBOSE"] = "1"

    if shallUseDirectConstantBlobs():
        mapping["NUITKA_USE_DIRECT_CONSTANT_BLOBS"] = "1"

    blob_filename = getConstantBlobFilename(source_dir)

    # This ends up being "__constants.txt" right now.
    stats_filename = changeFilenameExtension(blob_filename, ".txt")

    with withEnvironmentVarsOverridden(mapping):
        try:
            if not isRunningInInterpreter():
                executable = sys.modules["__main__"].__compiled__.original_argv0
                command = (
                    "DataComposer",
                    source_dir,
                    blob_filename,
                    stats_filename,
                )
            else:
                command = (
                    sys.executable,
                    data_composer_path,
                    source_dir,
                    blob_filename,
                    stats_filename,
                )
                executable = None

            subprocess.check_call(
                command,
                executable=executable,
                shell=False,
            )
        except subprocess.CalledProcessError as e:
            return data_composer_logger.sysexit(
                "Error executing data composer, exit code %d." % e.returncode
            )

    return getConstantBlobFilenames(source_dir), loadJsonFromFilename(stats_filename)


def getConstantBlobDirectory(source_dir):
    result = getNormalizedPathJoin(source_dir, "blobs")
    makePath(result)
    return result


def getConstantBlobFilename(source_dir):
    result = getNormalizedPathJoin(
        getConstantBlobDirectory(source_dir), "__constant.bin"
    )
    makeContainingPath(result)
    return result


def getConstantBlobFilenameForDataFilename(source_dir, data_filename):
    assert data_filename.endswith(".const"), data_filename

    result = getNormalizedPathJoin(
        getConstantBlobDirectory(source_dir),
        os.path.basename(changeFilenameExtension(data_filename, ".bin")),
    )
    makeContainingPath(result)
    return result


def getConstantBlobFilenames(source_dir):
    result = []

    blobs_dir = getConstantBlobDirectory(source_dir)

    for filename in os.listdir(blobs_dir):
        if filename.endswith(".bin"):
            result.append(getNormalizedPathJoin(blobs_dir, filename))

    return tuple(sorted(result))


def getConstantBlobSymbolBase(filename):
    basename = os.path.basename(filename)

    if basename.endswith(".const"):
        basename = basename[:-6]
    elif basename.endswith(".bin"):
        basename = basename[:-4]
    else:
        assert False, filename

    if basename.startswith("__"):
        basename = basename[2:]

    result = _constant_blob_symbol_bases.get(basename)

    if result is None:
        result = encodePythonIdentifierToC(basename)

        if result[0].isdigit():
            result = "_" + result

        origin = _constant_blob_symbol_origins.get(result)

        if origin is not None and origin != basename:
            return data_composer_logger.sysexit(
                "Error, constant blob names '%s' and '%s' collide on symbol base '%s'."
                % (origin, basename, result)
            )

        _constant_blob_symbol_bases[basename] = result
        _constant_blob_symbol_origins[result] = basename

    return result


def getConstantBlobSymbolName(filename):
    return getConstantBlobSymbolBase(filename) + "_bin"


def deriveModuleConstantsBlobName(filename):
    assert filename.endswith(".const")

    basename = filename[:-6]

    if basename == "__constants":
        return ""
    elif basename == "__bytecode":
        return ".bytecode"
    elif basename == "__files":
        return ".files"
    else:
        # Strip "module." prefix"
        basename = basename[7:]

        return basename


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
