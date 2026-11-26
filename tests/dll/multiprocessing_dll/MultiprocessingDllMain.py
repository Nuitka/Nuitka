#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-project: --mode=dll

from __future__ import print_function

import multiprocessing
import os
import sys


def computeSquare(value):
    return value * value


def main():
    if (
        "__compiled__" not in globals()
        and os.environ.pop("NUITKA_DLL_PARENT_MOCK", None) == "1"
    ):
        print("Host initialized with config: host_cfg_value")

    assert sys.argv[1:] == ["--worker-arg=ok"], sys.argv

    pool = multiprocessing.Pool(2)
    try:
        results = pool.map(computeSquare, [3, 7])
    finally:
        pool.close()
        pool.join()

    assert results == [9, 49], results
    print("Multiprocessing results:", results)
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
