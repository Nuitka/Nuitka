#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Standard plug-in to find data files.

"""

import os

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase

known_data_files = {
    "nose.core" : ("usage.txt",),
    "scrapy"    : ("VERSION",),
}

class NuitkaPluginDataFileCollector(NuitkaPluginBase):
    plugin_name = "data-files"

    @staticmethod
    def isRelevant():
        return Options.isStandaloneMode()

    def considerDataFiles(self, module):
        if module.getFullName() in known_data_files:
            for filename in known_data_files[module.getFullName()]:
                source_path = os.path.join(
                    os.path.dirname(module.getCompileTimeFilename()),
                    filename
                )

                if os.path.isfile(source_path):
                    yield (
                        source_path,
                        os.path.normpath(
                            os.path.join(
                                module.getFullName().replace('.', os.path.sep),
                                filename
                            )
                        )
                    )
