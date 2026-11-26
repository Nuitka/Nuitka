#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-project: --mode=dll
# nuitka-project: --output-filename=custom_host_dll
# nuitka-project-if: {OS} == "Windows":
#    nuitka-project: --windows-console-mode=hide

from __future__ import print_function

import atexit
import os
import sys
import threading
import time


def _onHostMockAfterFinalize():
    print("Host continuing after Python thread returned: 0")


def _onPythonAtExit():
    print("Python atexit cleanup ran.")


def main():
    if (
        "__compiled__" not in globals()
        and os.environ.pop("NUITKA_DLL_HOST_MOCK", None) == "1"
    ):
        atexit.register(_onHostMockAfterFinalize)

    atexit.register(_onPythonAtExit)

    assert threading.current_thread().name == "MainThread", threading.current_thread()

    if "__compiled__" in globals():
        assert len(sys.argv) == 1 and sys.argv[0], sys.argv

        handshake_dir = os.environ["NUITKA_DLL_HANDSHAKE_DIR"]
        ping_filename = os.path.join(handshake_dir, "handshake.ping")
        pong_filename = os.path.join(handshake_dir, "handshake.pong")

        with open(ping_filename, "w") as ping_file:
            ping_file.write("PING\n")

        deadline = time.time() + 10.0
        response = ""
        while not response:
            try:
                with open(pong_filename, "r") as pong_file:
                    response = pong_file.read().strip()
            except (IOError, OSError):
                pass

            if not response:
                if time.time() > deadline:
                    sys.exit("Timed out waiting for native C host thread response.")
                time.sleep(0.01)
    else:
        response = "PONG"

    print("MainThread handshake:", response)
    print("OK.")
    sys.exit(0)


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
