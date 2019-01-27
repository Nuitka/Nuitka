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
""" Access to standard library distinction.

For code to be in the standard library means that it's not written by the
user for sure. We treat code differently based on that information, by e.g.
including as byte code.

To determine if a module from the standard library, we can abuse the attribute
"__file__" of the "os" module like it's done in "isStandardLibraryPath" of this
module.
"""

import os

from nuitka.utils.Utils import getOS


def getStandardLibraryPaths():
    """ Get the standard library paths.

    """

    # Using the function object to cache its result, avoiding global variable
    # usage.
    if not hasattr(getStandardLibraryPaths, "result"):
        os_filename = os.__file__
        if os_filename.endswith(".pyc"):
            os_filename = os_filename[:-1]

        os_path = os.path.normcase(
            os.path.dirname(os_filename)
        )

        stdlib_paths = set([os_path])

        # Happens for virtualenv situation, some modules will come from the link
        # this points to.
        if os.path.islink(os_filename):
            os_filename = os.readlink(os_filename)  # @UndefinedVariable
            stdlib_paths.add(
                os.path.normcase(
                    os.path.dirname(os_filename)
                )
            )

        # Another possibility is "orig-prefix.txt" file near the os.py, which
        # points to the original install.
        orig_prefix_filename = os.path.join(os_path, "orig-prefix.txt")

        if os.path.isfile(orig_prefix_filename):
            # Scan upwards, until we find a "bin" folder, with "activate" to
            # locate the structural path to be added. We do not know for sure
            # if there is a sub-directory under "lib" to use or not. So we try
            # to detect it.
            search = os_path
            lib_part = ""

            while os.path.splitdrive(search)[1] not in (os.path.sep, ""):
                if os.path.isfile(os.path.join(search,"bin/activate")) or \
                   os.path.isfile(os.path.join(search,"scripts/activate")):
                    break

                lib_part = os.path.join(os.path.basename(search), lib_part)

                search = os.path.dirname(search)

            assert search and lib_part

            stdlib_paths.add(
                os.path.normcase(
                    os.path.join(
                        open(orig_prefix_filename).read(),
                        lib_part,
                    )
                )
            )

        # And yet another possibility, for macOS Homebrew created virtualenv
        # at least is a link ".Python", which points to the original install.
        python_link_filename = os.path.join(os_path, "..", ".Python")
        if os.path.islink(python_link_filename):
            stdlib_paths.add(
                os.path.normcase(
                    os.path.join(
                        os.readlink(python_link_filename),  # @UndefinedVariable
                        "lib"
                    )
                )
            )

        for stdlib_path in set(stdlib_paths):
            candidate = os.path.join(stdlib_path, "lib-tk")

            if os.path.isdir(candidate):
                stdlib_paths.add(candidate)

        if getOS() == "Windows":
            import _ctypes
            stdlib_paths.add(
                os.path.dirname(_ctypes.__file__)
            )

        getStandardLibraryPaths.result = [
            os.path.normcase(stdlib_path)
            for stdlib_path in
            stdlib_paths
        ]

    return getStandardLibraryPaths.result


def isStandardLibraryPath(path):
    """ Check if a path is in the standard library.

    """

    path = os.path.normcase(path)

    # In virtualenv, the "site.py" lives in a place that suggests it is not in
    # standard library, although it is.
    if os.path.basename(path) == "site.py":
        return True

    # These never are in standard library paths.
    if "dist-packages" in path or "site-packages" in path:
        return False

    for candidate in getStandardLibraryPaths():
        if path.startswith(candidate):
            return True

    return False
