#!/usr/bin/env python
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

""" Generated API documentation for Nuitka source.

"""

import os
import shutil
import stat
import sys
from optparse import OptionParser

from nuitka.tools.Basics import goHome
from nuitka.Tracing import my_print
from nuitka.utils.Execution import (
    check_call,
    getExecutablePath,
    withEnvironmentPathAdded,
)
from nuitka.utils.FileOperations import getFileContents, withTemporaryFile
from nuitka.utils.Utils import getOS


def main():
    goHome()

    parser = OptionParser()

    parser.add_option(
        "--upload",
        action="store_true",
        dest="upload",
        default=False,
        help="""\
Upload to https://nuitka.net/apidoc requires access rights and is done by the
official servers automatically only. Without this, create the local html folder
only.

Default is %default.""",
    )

    options, _positional_args = parser.parse_args()

    shutil.rmtree("html", ignore_errors=True)

    doxygen_path = getExecutablePath("doxygen")

    # Extra ball on Windows, check default installation PATH too.
    if not doxygen_path and getOS() == "Windows":
        with withEnvironmentPathAdded("PATH", r"C:\Program Files\Doxygen\bin"):
            doxygen_path = getExecutablePath("doxygen")

    if not doxygen_path:
        sys.exit("Error, need to install Doxygen and add it to PATH for this to work.")

    try:
        import doxypypy  # pylint: disable=I0021,unused-import,unused-variable
    except ImportError:
        sys.exit("Error, needs to install doxypypy into this Python.")

    with withTemporaryFile(suffix=".doxyfile", delete=False) as doxy_file:
        doxy_config = getFileContents("doc/Doxyfile.template")

        with withTemporaryFile(
            suffix=".bat" if getOS() == "Windows" else ".sh", delete=False
        ) as doxy_batch_file:
            if getOS() == "Windows":
                doxy_batch_file.write(
                    "%s -m doxypypy.doxypypy -a -c %%1" % sys.executable
                )
            else:
                doxy_batch_file.write(
                    "#!/bin/sh\nexec '%s' -m doxypypy.doxypypy -a -c $1"
                    % sys.executable
                )

        doxy_batch_filename = doxy_batch_file.name

        st = os.stat(doxy_batch_filename)
        os.chmod(doxy_batch_filename, st.st_mode | stat.S_IEXEC)

        doxy_config = doxy_config.replace("%DOXYPYPY%", doxy_batch_filename)
        doxy_file.write(doxy_config)

        doxy_filename = doxy_file.name

    my_print("Running doxygen:", style="blue")
    try:
        check_call([doxygen_path, doxy_filename])
    finally:
        os.unlink(doxy_filename)
        os.unlink(doxy_batch_filename)

    # Update the repository on the web site.
    if options.upload:
        assert (
            os.system(
                "rsync -avz --delete html/ --chown www-data root@ssh.nuitka.net:/var/www/apidoc/"
            )
            == 0
        )

    my_print("Finished.", style="blue")


if __name__ == "__main__":
    main()
