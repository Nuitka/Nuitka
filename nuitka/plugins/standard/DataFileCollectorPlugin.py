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
    "nose.core" : (
        (None, "usage.txt"),
    ),
    "scrapy"    : (
        (None, "VERSION"),
    ),
    "requests"  : (
        ("certifi", "../certifi/cacert.pem"),
    )
}

class NuitkaPluginDataFileCollector(NuitkaPluginBase):
    plugin_name = "data-files"

    @staticmethod
    def isRelevant():
        return Options.isStandaloneMode()

    def considerDataFiles(self, module):
        if module.getFullName() in known_data_files:
            for target_dir, filename in known_data_files[module.getFullName()]:
                source_path = os.path.join(
                    os.path.dirname(module.getCompileTimeFilename()),
                    filename
                )

                if os.path.isfile(source_path):
                    if target_dir is None:
                        target_dir = module.getFullName().replace('.', os.path.sep)

                    yield (
                        source_path,
                        os.path.normpath(
                            os.path.join(
                                target_dir,
                                filename
                            )
                        )
                    )
