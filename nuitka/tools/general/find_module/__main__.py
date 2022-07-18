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
""" Tool to find and report module location.

"""

import os
import sys

from nuitka.importing.Importing import (
    ModuleName,
    locateModule,
    setMainScriptDirectory,
)
from nuitka.Tracing import my_print


def main():
    module_name = ModuleName(sys.argv[1])

    setMainScriptDirectory(os.getcwd())

    my_print(
        " ".join(locateModule(module_name=module_name, parent_package=None, level=0))
    )


if __name__ == "__main__":
    main()
