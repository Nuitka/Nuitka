#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" TkInter standalone test, trying to make sure it loads.

"""

# nuitka-skip-unless-expression: __import__("Tkinter" if sys.version_info[0] < 3 else "tkinter")

# nuitka-project: --mode=standalone
# nuitka-project: --enable-plugin=tk-inter

# Make sure, the usual bad ones are not included with anti-bloat.

# nuitka-project: --noinclude-default-mode=error

from __future__ import print_function

import os
import sys

print("START:")
# os.chdir(os.path.dirname(__file__))
# print(os.getcwd())

# Python3 changed module name.
if str is bytes:
    import Tkinter as tkinter
else:
    import tkinter

print("Imported tkinter.")

try:
    root = tkinter.Tk()  # this will fail in absence of TCL
except tkinter.TclError as e:
    assert "connect to display" in str(e) or "no display" in str(e), str(e)
    print("TCLError exception happened.")
    sys.exit(0)
else:
    print("Imported tkinter module.")

try:
    import tkinter.tix
except ImportError:
    print("No tix found.")
else:
    print("Imported tkinter tix module.")

try:
    import tkinter.ttk
except ImportError:
    print("No ttk found.")
else:
    print("Imported tkinter ttk module.")


print("OK.")

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
