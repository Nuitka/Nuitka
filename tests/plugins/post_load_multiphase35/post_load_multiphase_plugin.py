#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""User plugin exercising post-load code on a multi-phase extension module."""

from nuitka.plugins.PluginBase import NuitkaPluginBase


class NuitkaPluginForTesting(NuitkaPluginBase):
    plugin_name = "post-load-multiphase"

    @staticmethod
    def createPostModuleLoadCode(module):
        # spell-checker: ignore testmultiphase
        if module.getFullName() == "_testmultiphase":
            return (
                """\
from __future__ import absolute_import
from _testmultiphase import Example

assert Example.__name__ == "Example"
""",
                """\
Verify post-load code for multi-phase extension modules runs after execution.""",
            )


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
