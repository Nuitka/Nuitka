#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Interface to depends.exe on Windows.

We use depends.exe to investigate needed DLLs of Python DLLs.

"""

import os
import sys
from logging import info

from nuitka import Tracing
from nuitka.__past__ import raw_input, urlretrieve  # pylint: disable=W0622
from nuitka.utils import Utils


def getDependsExePath():
    """ Return the path of depends.exe (for Windows).

        Will prompt the user to download if not already cached in AppData
        directory for Nuitka.
    """
    if Utils.getArchitecture() == "x86":
        depends_url = "http://dependencywalker.com/depends22_x86.zip"
    else:
        depends_url = "http://dependencywalker.com/depends22_x64.zip"

    if "APPDATA" not in os.environ:
        sys.exit("Error, standalone mode cannot find 'APPDATA' environment.")

    nuitka_app_dir = Utils.joinpath(os.environ["APPDATA"], "nuitka")
    if not Utils.isDir(nuitka_app_dir):
        Utils.makePath(nuitka_app_dir)

    nuitka_depends_zip = Utils.joinpath(
        nuitka_app_dir,
        Utils.basename(depends_url)
    )

    if not Utils.isFile(nuitka_depends_zip):
        Tracing.printLine("""\
Nuitka will make use of Dependency Walker (http://dependencywalker.com) tool
to analyze the dependencies of Python extension modules. Is it OK to download
and put it in APPDATA (no installer needed, cached, one time question).""")

        reply = raw_input("Proceed and download? [Yes]/No ")

        if reply.lower() in ("no", 'n'):
            sys.exit("Nuitka does not work in --standalone on Windows without.")

        info("Downloading '%s'" % depends_url)

        urlretrieve(
            depends_url,
            nuitka_depends_zip
        )

    nuitka_depends_dir = Utils.joinpath(
        nuitka_app_dir,
        Utils.getArchitecture()
    )

    if not Utils.isDir(nuitka_depends_dir):
        os.makedirs(nuitka_depends_dir)

    depends_exe = os.path.join(
        nuitka_depends_dir,
        "depends.exe"
    )

    if not Utils.isFile(depends_exe):
        info("Extracting to '%s'" % depends_exe)

        import zipfile

        try:
            depends_zip = zipfile.ZipFile(nuitka_depends_zip)
            depends_zip.extractall(nuitka_depends_dir)
        except Exception: # Catching anything zip throws, pylint:disable=W0703
            info("Problem with the downloaded zip file, deleting it.")

            Utils.deleteFile(depends_exe, must_exist = False)
            Utils.deleteFile(nuitka_depends_zip, must_exist = True)

            sys.exit(
                "Error, need '%s' as extracted from '%s'." % (
                    depends_exe,
                    depends_url
                )
            )

    assert Utils.isFile(depends_exe)

    return depends_exe
