#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-project: --mode=dll
# nuitka-project: --dll-header-language=rust,C
# nuitka-project: --product-version=1.2.3.4
# nuitka-project: --file-version=1.2.3.4
# nuitka-project: --include-data-files={MAIN_DIRECTORY}/bundled_data.txt=bundled_data.txt

from __future__ import print_function

import os
import sys
import unicodedata

import helper_module


def main():
    if len(sys.argv) == 2 and sys.argv[1].startswith("--exit-code="):
        sys.exit(int(sys.argv[1].split("=", 1)[1]))

    if len(sys.argv) == 2 and sys.argv[1].startswith("--exit-message="):
        sys.exit(sys.argv[1].split("=", 1)[1])

    print("Helper:", helper_module.getMessage())
    print("Unicode lookup:", unicodedata.name("A"))
    print("Arguments:", sys.argv[1:])

    data_filename = os.path.join(os.path.dirname(__file__), "bundled_data.txt")
    with open(data_filename, "r") as data_file:
        print("Data file:", data_file.read().strip())

    if "__compiled__" in globals():
        assert __compiled__.standalone is True, __compiled__
        assert __compiled__.onefile is False, __compiled__
        assert __compiled__.module is False, __compiled__
        assert __compiled__.dll is True, __compiled__
        assert __compiled__.extension_filename is None, __compiled__
        assert __compiled__.process_exe is None, __compiled__
        assert os.path.isfile(__compiled__.dll_filename), __compiled__.dll_filename
        assert (
            os.path.dirname(__compiled__.dll_filename)
            == __compiled__.python_runtime_dir
        ), __compiled__

        runtime_data_filename = os.path.join(
            __compiled__.python_runtime_dir, "bundled_data.txt"
        )
        assert os.path.isfile(runtime_data_filename), runtime_data_filename
        assert os.path.isdir(__compiled__.containing_dir), __compiled__.containing_dir

    print("OK.")


if __name__ == "__main__":
    main()

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
