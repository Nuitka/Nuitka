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
""" Standard plug-in to make pbr module work when compiled.

The pbr module needs to find a version number in compiled mode. The value
itself seems less important than the fact that some value does exist.
"""

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginPbrWorkarounds(NuitkaPluginBase):
    """This is to make pbr module work when compiled with Nuitka."""

    plugin_name = "pbr-compat"

    @classmethod
    def isRelevant(cls):
        return Options.isStandaloneMode()

    @staticmethod
    def isAlwaysEnabled():
        return True

    @staticmethod
    def createPreModuleLoadCode(module):
        full_name = module.getFullName()

        if full_name == "pbr.packaging":
            code = """\
import os
version = os.environ.get(
        "PBR_VERSION",
        os.environ.get("OSLO_PACKAGE_VERSION"))
if not version:
    os.environ["OSLO_PACKAGE_VERSION"] = "1.0"
"""
            return (
                code,
                """\
Monkey patching "pbr" version number.""",
            )
