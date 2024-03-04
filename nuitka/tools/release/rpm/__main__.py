#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" OpenSUSE Build Service (OSC) upload release tool.

Uploads Nuitka branches adapting the RPM configuration to the different
projects on OSC.
"""

import os
import shutil
import sys

from nuitka.tools.Basics import goHome
from nuitka.tools.release.Release import checkBranchName
from nuitka.Tracing import tools_logger
from nuitka.utils.FileOperations import (
    getFileContents,
    makePath,
    putTextFileContents,
    renameFile,
    withDirectoryChange,
)
from nuitka.Version import getNuitkaVersion


def main():
    goHome()

    nuitka_version = getNuitkaVersion()
    branch_name = checkBranchName()

    shutil.rmtree("build", ignore_errors=True)
    makePath("build")

    # Used by rpmbuild
    makePath(os.path.expanduser("~/rpmbuild/SOURCES"))

    # Upload stable releases to OpenSUSE Build Service:
    if (
        branch_name.startswith("release")
        or branch_name.startswith("hotfix")
        or branch_name == "main"
    ):
        rpm_project_name = "Nuitka"
        spec_suffix = ""
    elif branch_name == "develop":
        rpm_project_name = "Nuitka-Develop"
        spec_suffix = "-develop"
    elif branch_name == "factory":
        rpm_project_name = "Nuitka-Factory"
        spec_suffix = "-factory"
    else:
        tools_logger.sysexit("Skipping RPM build for branch '%s'" % branch_name)

    with withDirectoryChange("build"):
        tools_logger.info(
            "Building source distribution for %s %s"
            % (rpm_project_name, nuitka_version)
        )
        assert os.system("%s ../setup.py sdist --formats=gztar" % sys.executable) == 0
        nuitka_dist_filename = "Nuitka%s-%s.tar.gz" % (spec_suffix, nuitka_version)
        renameFile(
            source_filename=os.path.join("..", "dist", nuitka_dist_filename),
            dest_filename=os.path.join("/root/rpmbuild/SOURCES", nuitka_dist_filename),
        )

        # Adapt the spec file dynamically to version and project name of Nuitka being built.
        spec_contents = getFileContents(
            os.path.join(os.path.dirname(__file__), "nuitka.spec")
        )
        spec_contents = spec_contents.replace("PROJECT_NAME", "nuitka" + spec_suffix)
        spec_contents = spec_contents.replace("PROJECT_VERSION", nuitka_version)

        spec_filename = "nuitka%s.spec" % spec_suffix
        putTextFileContents(
            filename=spec_filename,
            contents=spec_contents,
        )

        os.system("rpmbuild --target x86_64 -bb %s" % spec_filename)


if __name__ == "__main__":
    main()

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
