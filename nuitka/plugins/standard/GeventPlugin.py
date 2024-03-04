#     Copyright 2024, Jorj McKie, mailto:<jorj.x.mckie@outlook.de> find license text at end of file


""" Details see below in class definition.
"""

from nuitka import Options
from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginGevent(NuitkaPluginBase):
    """This class represents the main logic of the plugin."""

    plugin_name = "gevent"
    plugin_desc = "Required by the 'gevent' package."

    # TODO: Change this to Yaml configuration.

    @staticmethod
    def isAlwaysEnabled():
        return True

    @classmethod
    def isRelevant(cls):
        """One time only check: may this plugin be required?

        Returns:
            True if this is a standalone compilation.
        """
        return Options.isStandaloneMode()

    @staticmethod
    def createPostModuleLoadCode(module):
        """Make sure greentlet tree tracking is switched off."""
        full_name = module.getFullName()

        if full_name == "gevent":
            code = r"""\
import gevent._config
gevent._config.config.track_greenlet_tree = False
"""

            return (
                code,
                """\
Disabling 'gevent' greenlet tree tracking.""",
            )


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
