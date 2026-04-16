#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Generate header files that provide compiler specifics."""

import os

from nuitka.build.AdaptPythonHeaderFiles import getOffsetsJsonRequiredKeys
from nuitka.build.SconsInterface import (
    cleanSconsDirectory,
    getCommonSconsOptions,
    runScons,
)
from nuitka.PythonVersions import isPythonWithGil, python_version_str
from nuitka.tools.quality.auto_format.AutoFormat import (
    withFileOpenedAndAutoFormatted,
)
from nuitka.Tracing import offsets_logger
from nuitka.utils.Execution import check_output
from nuitka.utils.FileOperations import (
    getNormalizedPath,
    makeContainingPath,
    makePath,
    putTextFileContents,
    withTemporaryFilename,
)
from nuitka.utils.Jinja2 import getTemplateC
from nuitka.utils.PrivatePipSpace import getZigBinaryPath
from nuitka.utils.Utils import getArchitecture, getOS


def getPythonInternalsOffsetDir():
    """Return the source distribution bundled JSON storage path resolving strictly against this module."""

    return getNormalizedPath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "build",
            "python_internal_offset",
        )
    )


def generateHeader():
    scons_options, env_values = getCommonSconsOptions()

    if getOS() == "Windows":
        scons_options["zig_exe_path"] = getZigBinaryPath(
            logger=offsets_logger,
            assume_yes_for_downloads=True,
            reject_message="Nuitka needs zig for header generation.",
        )
        if scons_options["zig_exe_path"] is None:
            return offsets_logger.sysexit("Nuitka needs zig for header generation.")

    scons_options["source_dir"] = "generate_header.build"
    cleanSconsDirectory(scons_options["source_dir"])
    makePath(scons_options["source_dir"])

    keys = getOffsetsJsonRequiredKeys(python_version_str)

    template = getTemplateC(
        package_name="nuitka.tools.general.generate_header",
        template_name="GenerateHeadersMain.c.j2",
    )

    c_code = template.render(keys=keys)

    c_filepath = os.path.join(
        scons_options["source_dir"],
        "static_src",
        "GenerateHeadersMain.c",
    )
    makeContainingPath(c_filepath)
    putTextFileContents(c_filepath, c_code)

    python_version_id = "%s-%s-%s-%s" % (
        python_version_str,
        getOS(),
        getArchitecture(),
        "gil" if isPythonWithGil() else "no-gil",
    )

    with withTemporaryFilename(prefix=python_version_id, suffix=".exe") as result_exe:
        scons_options["result_exe"] = result_exe

        success = runScons(
            scons_options=scons_options,
            env_values=env_values,
            scons_filename="Offsets.scons",
        )

        if not success:
            return offsets_logger.sysexit(
                "Error, failed to compile offsets generation program."
            )

        header_output = check_output([result_exe])

        if str is not bytes:
            header_output = header_output.decode("utf8")

        lines = [line.strip() for line in header_output.splitlines() if line.strip()]

        json_filename = os.path.join(
            getPythonInternalsOffsetDir(),
            "offsets_%s.json" % python_version_id,
        )

        makeContainingPath(json_filename)

        with withFileOpenedAndAutoFormatted(
            json_filename, effective_filename=json_filename
        ) as output_f:
            output_f.write("".join(lines))

        offsets_logger.info("Gathered offsets into %s" % json_filename)
        offsets_logger.info("OK.")


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
