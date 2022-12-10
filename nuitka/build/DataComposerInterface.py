#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Interface to data composer

"""
import os
import subprocess
import sys

from nuitka.Options import isExperimental
from nuitka.utils.Execution import withEnvironmentVarsOverridden


def runDataComposer(source_dir):
    from nuitka.plugins.Plugins import Plugins

    Plugins.onDataComposerRun()
    blob_filename = _runDataComposer(source_dir=source_dir)
    Plugins.onDataComposerResult(blob_filename)


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

    with withEnvironmentVarsOverridden(mapping):
        subprocess.check_call(
            [
                sys.executable,
                data_composer_path,
                source_dir,
                blob_filename,
            ],
            shell=False,
        )

    return blob_filename


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
