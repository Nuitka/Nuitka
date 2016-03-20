#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Plugin to pre-process PMW for inclusion.

"""

import os
import re
import sys

from nuitka import Options
from nuitka.__past__ import StringIO
from nuitka.plugins.PluginBase import NuitkaPluginBase

# The main logic of this is from StackOverflow answer:
# http://stackoverflow.com/questions/6772916/python-pmw-and-cx-freeze


# The order of these files is significant.  Files which reference
# other files must appear later.  Files may be deleted if they are not
# used.
files = [
    "Dialog", "TimeFuncs", "Balloon", "ButtonBox", "EntryField",
    "Group", "LabeledWidget", "MainMenuBar", "MenuBar", "MessageBar",
    "MessageDialog", "NoteBook", "OptionMenu", "PanedWidget", "PromptDialog",
    "RadioSelect", "ScrolledCanvas", "ScrolledField", "ScrolledFrame",
    "ScrolledListBox", "ScrolledText", "HistoryText", "SelectionDialog",
    "TextDialog", "TimeCounter", "AboutDialog", "ComboBox", "ComboBoxDialog",
    "Counter", "CounterDialog",
]

# Work out which version is being bundled.

class NuitkaPluginPmw(NuitkaPluginBase):
    plugin_name = "pmw-freezer"

    def onModuleSourceCode(self, module_name, source_code):
        if module_name == "Pmw":
            pmw_path = self.locateModule(
                importing      = None,
                module_name    = "Pmw",
                module_package = None
            )

            return self._packagePmw(pmw_path)

        return source_code

    def _packagePmw(self, pmw_path):
        # From the "__init__.py" of Pwm:
        def _hasLoader(dirname):  # @ReservedAssignment
            # Only accept Pmw_V_R_P with single digits, since ordering will
            # not work correctly with multiple digits (for example, Pmw_10_0
            # will be before Pmw_9_9).
            if re.search("^Pmw_[0-9]_[0-9](_[0-9])?$", dirname) is not None:
                for suffix in (".py", ".pyc", ".pyo"):
                    path = os.path.join(pmw_path, dirname, "lib", "PmwLoader" + suffix)
                    if os.path.isfile(path):
                        return 1
            return 0

        # This mimicks the scan the __init__.py does.
        candidates = []
        for candidate in os.listdir(pmw_path):
            if _hasLoader(candidate):
                candidates.append(candidate)

        candidates.sort()
        candidates.reverse()

        if not candidates:
            sys.exit("Error, cannot find any Pmw versions.")

        candidate = os.path.join(pmw_path, candidates[0], "lib")
        version = candidates[0][4:].replace('_', '.')

        return self._packagePmw2(candidate, version)

    def _packagePmw2(self, srcdir, version):
        def mungeFile(filename):
            # Read the filename and modify it so that it can be bundled with the
            # other Pmw files.
            filename = "Pmw" + filename + ".py"
            text = open(os.path.join(srcdir, filename)).read()
            text = re.sub(r"import Pmw\>", "", text)
            text = re.sub("INITOPT = Pmw.INITOPT", "", text)
            text = re.sub(r"\<Pmw\.", "", text)
            text = '\n' + ('#' * 70) + '\n' + "### File: " + filename + '\n' + text
            return text

        # Code to import the Color module.
        colorCode = """
import PmwColor
Color = PmwColor
del PmwColor
"""
        # Code to import the Blt module.
        bltCode = """
import PmwBlt
Blt = PmwBlt
del PmwBlt
"""
        # Code used when not linking with PmwBlt.py.
        ignoreBltCode = """
_bltImported = 1
_bltbusyOK = 0
"""
        # Code to define the functions normally supplied by the dynamic loader.
        extraCode = """

### Loader functions:

_VERSION = '%s'

def setversion(version):
    if version != _VERSION:
        raise ValueError, 'Dynamic versioning not available'

def setalphaversions(*alpha_versions):
    if alpha_versions != ():
        raise ValueError, 'Dynamic versioning not available'

def version(alpha = 0):
    if alpha:
        return ()
    else:
        return _VERSION

def installedversions(alpha = 0):
    if alpha:
        return ()
    else:
        return (_VERSION,)

"""

        # Set this to 0 if you do not use any of the Pmw.Color functions:
        # Set this to 0 if you do not use any of the Pmw.Blt functions:
        needBlt = not self.getPluginOptionBool("noblt", True)
        needColor = not self.getPluginOptionBool("nocolor", True)

        outfile = StringIO()

        if needColor:
            outfile.write(colorCode)

        if needBlt:
            outfile.write(bltCode)

        outfile.write(extraCode % version)

        # Specially handle PmwBase.py filename:
        text = mungeFile("Base")
        text = re.sub("import PmwLogicalFont", "", text)
        text = re.sub("PmwLogicalFont._font_initialise", "_font_initialise", text)
        outfile.write(text)
        if not needBlt:
            outfile.write(ignoreBltCode)

        files.append("LogicalFont")

        for filename in files:
            text = mungeFile(filename)
            outfile.write(text)

        return outfile.getvalue()


class NuitkaPluginDetectorPmw(NuitkaPluginBase):
    plugin_name = "pmw-freezer"

    @staticmethod
    def isRelevant():
        return Options.isStandaloneMode()

    def onModuleDiscovered(self, module):
        if module.getFullName() == "Pmw":
            self.warnUnusedPlugin("Proper freezing of Pmw package.")
