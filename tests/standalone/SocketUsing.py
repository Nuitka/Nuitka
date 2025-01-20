# -*- coding: utf-8 -*-
#     Copyright 2025, Paweł Kierzkowski, mailto:<pk.pawelo@gmail.com> find license text at end of file


""" Test that shows that the socket module can properly be used.

"""

# nuitka-project: --mode=standalone

import signal
import socket
import sys


# Set up a timeout, seems to happen that below call stalls.
def onTimeout(_signum, _frame):
    sys.exit(0)


# Not available on Windows, but there we didn't see the problem anyway,
# not going to make this use threading for now.
try:
    signal.signal(signal.SIGALRM, onTimeout)
    signal.alarm(1)
except AttributeError:
    pass


# Call to socket.getfqdn with a non-local address will cause libresolv.so glibc
# library to be loaded
socket.getfqdn("1.1.1.1")

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
