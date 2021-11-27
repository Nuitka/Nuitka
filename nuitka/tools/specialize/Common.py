#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Common helper functions for specializing code."""
import contextlib
import os
import shutil

from nuitka.tools.quality.autoformat.Autoformat import autoformat
from nuitka.Tracing import my_print
from nuitka.utils.FileOperations import openTextFile


@contextlib.contextmanager
def withFileOpenedAndAutoformatted(filename):
    my_print("Creating %r ..." % filename)

    tmp_filename = filename + ".tmp"
    with openTextFile(tmp_filename, "w") as output:
        yield output

    autoformat(
        filename=tmp_filename, git_stage=None, effective_filename=filename, trace=False
    )

    # No idea why, but this helps.
    if os.name == "nt":
        autoformat(
            filename=tmp_filename,
            git_stage=None,
            effective_filename=filename,
            trace=False,
        )

    shutil.copy(tmp_filename, filename)
    os.unlink(tmp_filename)


def writeline(output, *args):
    if not args:
        output.write("\n")
    elif len(args) == 1:
        output.write(args[0] + "\n")
    else:
        assert False, args
