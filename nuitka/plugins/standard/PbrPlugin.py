#     Copyright 2025, Jorj McKie, mailto:<jorj.x.mckie@outlook.de> find license text at end of file


"""Standard plug-in to make pbr module work when compiled.

The pbr module needs to find a version number in compiled mode. The value
itself seems less important than the fact that some value does exist.
"""

from nuitka.options.Options import isStandaloneMode
from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginPbrWorkarounds(NuitkaPluginBase):
    """This is to make pbr module work when compiled with Nuitka."""

    plugin_name = "pbr-compat"
    plugin_desc = "Required by 'pbr' package."
    plugin_category = "package-support"

    @classmethod
    def isRelevant(cls):
        return isStandaloneMode()

    @staticmethod
    def isAlwaysEnabled():
        return True

    @staticmethod
    def createPreModuleLoadCode(module):
        full_name = module.getFullName()

        if full_name == "pbr.packaging":
            code = """\
import os
version = os.getenv(
        "PBR_VERSION",
        os.getenv("OSLO_PACKAGE_VERSION"))
if not version:
    os.environ["OSLO_PACKAGE_VERSION"] = "1.0"
"""
            return (
                code,
                """\
Monkey patching "pbr" version number.""",
            )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
