#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Internal tool, attach the standalone distribution in compressed form.

"""

import os
import sys

if __name__ == "__main__":
    sys.path.insert(0, os.environ["NUITKA_PACKAGE_HOME"])

    import nuitka  # just to have it loaded from there, pylint: disable=unused-import

    del sys.path[0]

    sys.path = [
        path_element
        for path_element in sys.path
        if os.path.dirname(os.path.abspath(__file__)) != path_element
    ]

    from nuitka.tools.onefile_compressor.OnefileCompressor import main

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
