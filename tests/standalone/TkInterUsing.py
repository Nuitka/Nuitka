#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
""" TkInter standalone test, trying to make sure it loads.

"""

# nuitka-project: --standalone
# nuitka-project: --enable-plugin=tk-inter

from __future__ import print_function

# Python3 changed module name.
if str is bytes:
    import Tkinter as tkinter
else:
    import tkinter

# nuitka-skip-unless-expression: __import__("Tkinter" if sys.version_info[0] < 3 else "tkinter")

try:
    root = tkinter.Tk()  # this will fail in absence of TCL
except tkinter.TclError as e:
    print("TCLError exception happened.")
    assert "connect to display" in str(e) or "no display" in str(e), str(e)
else:
    print("OK")
