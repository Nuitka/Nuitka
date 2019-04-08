#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Release: Create and upload Windows MSI files for Nuitka

"""

from __future__ import print_function

import os
import subprocess

from nuitka.tools.release.MSI import createMSIPackage


def main():
    msi_filename = createMSIPackage()

    assert (
        subprocess.call(
            (
                "scp",
                msi_filename,
                "git@nuitka.net:/var/www/releases/" + os.path.basename(msi_filename),
            ),
            shell=True,  # scan scp in PATH.
        )
        == 0
    )

    print("OK, uploaded", msi_filename)


if __name__ == "__main__":
    main()
