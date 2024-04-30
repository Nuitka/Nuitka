#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Interface to data composer

"""

import os
import subprocess
import sys

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.Options import isExperimental
from nuitka.Tracing import data_composer_logger
from nuitka.utils.Execution import withEnvironmentVarsOverridden
from nuitka.utils.FileOperations import changeFilenameExtension, getFileSize
from nuitka.utils.Json import loadJsonFromFilename

# Indicate not done with -1
_data_composer_size = None
_data_composer_stats = None


def getDataComposerReportValues():
    return OrderedDict(blob_size=_data_composer_size, stats=_data_composer_stats)


def runDataComposer(source_dir):
    from nuitka.plugins.Plugins import Plugins

    # This module is a singleton, pylint: disable=global-statement
    global _data_composer_stats

    Plugins.onDataComposerRun()
    blob_filename, _data_composer_stats = _runDataComposer(source_dir=source_dir)
    Plugins.onDataComposerResult(blob_filename)

    global _data_composer_size
    _data_composer_size = getFileSize(blob_filename)


def _runDataComposer(source_dir):
    data_composer_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "tools", "data_composer")
    )

    mapping = {
        "NUITKA_PACKAGE_HOME": os.path.dirname(
            os.path.abspath(sys.modules["nuitka"].__path__[0])
        )
    }

    if isExperimental("debug-constants"):
        mapping["NUITKA_DATA_COMPOSER_VERBOSE"] = "1"

    blob_filename = getConstantBlobFilename(source_dir)

    stats_filename = changeFilenameExtension(blob_filename, ".txt")

    with withEnvironmentVarsOverridden(mapping):
        try:
            subprocess.check_call(
                [
                    sys.executable,
                    data_composer_path,
                    source_dir,
                    blob_filename,
                    stats_filename,
                ],
                shell=False,
            )
        except subprocess.CalledProcessError:
            data_composer_logger.sysexit(
                "Error executing data composer, please report the above exception."
            )

    return blob_filename, loadJsonFromFilename(stats_filename)


def getConstantBlobFilename(source_dir):
    return os.path.join(source_dir, "__constants.bin")


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
