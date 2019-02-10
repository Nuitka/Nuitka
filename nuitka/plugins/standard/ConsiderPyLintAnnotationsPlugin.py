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
""" Standard plug-in to take advantage of pylint or PyDev annotations.

Nuitka can detect some things that PyLint and PyDev will complain about too,
and sometimes it's a false alarm, so people add disable markers into their
source code. Nuitka does it itself.

This tries to parse the code for these markers and uses hooks to prevent Nuitka
from warning about things, disabled to PyLint or Eclipse. The idea is that we
won't have another mechanism for Nuitka, but use existing ones instead.

The code for this is very incomplete, barely good enough to cover Nuitka's own
usage of PyLint markers. PyDev is still largely to be started. You are welcome
to grow both.

"""


import re

from nuitka.__past__ import intern  # pylint: disable=I0021,redefined-builtin
from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginPylintEclipseAnnotations(NuitkaPluginBase):
    plugin_name = "pylint-warnings"

    def __init__(self):
        self.line_annotations = {}

    def onModuleSourceCode(self, module_name, source_code):
        annotations = {}

        for count, line in enumerate(source_code.split("\n")):
            match = re.search(r"#.*pylint:\s*disable=\s*([\w,-]+)", line)

            if match:
                comment_only = line[: line.find("#") - 1].strip() == ""

                if comment_only:
                    # TODO: Parse block wide annotations too.
                    pass
                else:
                    annotations[count + 1] = set(
                        intern(match.strip()) for match in match.group(1).split(",")
                    )

        # Only remember them if there were any.
        if annotations:
            self.line_annotations[module_name] = annotations

        # Do nothing to it.
        return source_code

    def suppressUnknownImportWarning(self, importing, module_name, source_ref):
        annotations = self.line_annotations.get(importing.getFullName(), {})

        line_annotations = annotations.get(source_ref.getLineNumber(), ())

        if "F0401" in line_annotations or "import-error" in line_annotations:
            return True

        return False


class NuitkaPluginDetectorPylintEclipseAnnotations(NuitkaPluginBase):
    plugin_name = "pylint-warnings"

    @staticmethod
    def isRelevant():
        return True

    def onModuleSourceCode(self, module_name, source_code):
        if re.search(r"#\s*pylint:\s*disable=\s*(\w+)", source_code):
            self.warnUnusedPlugin("Understand PyLint/PyDev annotations for warnings.")

        # Do nothing to it.
        return source_code
