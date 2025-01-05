#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Parameter using Nuitka plugin.

"""

import os
import sys

# from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginForTesting(NuitkaPluginBase):
    plugin_name = __name__.split(".")[-1]

    def __init__(self, trace_my_plugin):
        # demo only: extract and display my options list
        # check whether some specific option is set

        self.check = trace_my_plugin
        self.info("The 'trace' value is set to '%s'" % self.check)

        # do more init work here ...

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--trace-my-plugin",
            action="store_true",
            dest="trace_my_plugin",
            default=False,
            help="This is show in help output.",
        )

    def onModuleSourceCode(self, module_name, source_filename, source_code):
        # if this is the main script and tracing should be done ...
        if module_name == "__main__" and self.check:
            self.info("")
            self.info(" Calls to 'math' module:")
            for i, l in enumerate(source_code.splitlines()):
                if "math." in l:
                    self.info(" %i: %s" % (i + 1, l))
            self.info("")
        return source_code


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
