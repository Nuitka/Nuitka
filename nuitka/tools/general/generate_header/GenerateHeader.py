#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Generate header files that provide compiler specifics."""

from nuitka.build.SconsInterface import (
    cleanSconsDirectory,
    getCommonSconsOptions,
    runScons,
    setPythonTargetOptions,
)
from nuitka.PythonVersions import isPythonWithGil, python_version_str
from nuitka.Tracing import offsets_logger
from nuitka.utils.Execution import check_output
from nuitka.utils.FileOperations import makePath, withTemporaryFilename


def generateHeader():
    scons_options, env_values = getCommonSconsOptions()

    setPythonTargetOptions(scons_options)

    scons_options["source_dir"] = "generate_header.build"
    cleanSconsDirectory(scons_options["source_dir"])
    makePath(scons_options["source_dir"])

    python_version_id = "%s_%s" % (
        python_version_str,
        "gil" if isPythonWithGil() else "no-gil",
    )

    with withTemporaryFilename(prefix=python_version_id, suffix=".exe") as result_exe:
        scons_options["result_exe"] = result_exe

        runScons(
            scons_options=scons_options,
            env_values=env_values,
            scons_filename="Offsets.scons",
        )

        header_output = check_output([result_exe])

        if str is not bytes:
            header_output = header_output.decode("utf8")

        offsets_logger.info(repr(header_output))

        lines = header_output.splitlines()

        if lines[-1] != "OK.":
            offsets_logger.sysexit("Error, failed to produce expected output.")
        del lines[-1]

        for line in lines:
            offsets_logger.info("Processing: %s" % line)

        offsets_logger.info("OK.")


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
