#!/usr/bin/python
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

import os
import shutil
import subprocess
import sys


def main():

    # Set the stage.
    os.chdir(os.path.dirname(__file__))
    shutil.rmtree("coverage", ignore_errors=True)

    print("Fetching coverage files:")

    subprocess.call(
        ["rsync", "-az", "--delete", "%s/" % os.environ["COVERAGE_DIR"], "coverage/"]
    )

    print("Combining coverage files:")
    os.chdir("coverage")

    print("Detect coverage file roots:")
    # Now detect where the files were collected from:

    paths = [os.path.abspath(os.path.join(os.curdir, "..", ".."))]

    for filename in os.listdir("."):
        if not filename.startswith("meta.coverage"):
            continue

        values = {}
        exec(open(filename).read(), values)
        if "__builtins__" in values:
            del values["__builtins__"]

        paths.append(values["NUITKA_SOURCE_DIR"])

    coverage_path = os.path.abspath(".coveragerc")

    with open(coverage_path, "w") as coverage_rcfile:
        coverage_rcfile.write("[paths]\n")
        coverage_rcfile.write("source = \n")

        for path in paths:
            coverage_rcfile.write("   " + path + "\n")

    subprocess.call(
        [sys.executable, "-m", "coverage", "combine", "--rcfile", coverage_path]
    )

    assert os.path.exists(coverage_path)

    subprocess.call(
        [sys.executable, "-m", "coverage", "html", "--rcfile", coverage_path]
    )

    # Clean up after ourselves again.
    # shutil.rmtree("coverage", ignore_errors = True)


if __name__ == "__main__":
    main()
