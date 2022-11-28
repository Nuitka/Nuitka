#     Copyright 2022, Jorj McKie, mailto:<jorj.x.mckie@outlook.de>
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
""" Details see below in class definition.
"""

from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginNumpy(NuitkaPluginBase):
    """This plugin is now not doing anything anymore."""

    plugin_name = "numpy"  # Nuitka knows us by this name
    plugin_desc = "Deprecated, was once required by the numpy package"

    @classmethod
    def isDeprecated(cls):
        return True
