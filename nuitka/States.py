#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""
Global states of Nuitka.

This is for options that are not really options, but reflect the state of the
compilation, e.g. if it's a debug compilation. These are easier to access
as a global instance.

"""


class GlobalState(object):
    """The global state of Nuitka compilation."""

    __slots__ = (
        "is_debug",
        "is_non_debug",
        "is_full_compat",
        "report_missing_code_helpers",
        "report_missing_trust",
        "is_verbose",
        "data_composer_verbose",
    )

    def __init__(self):
        self.is_debug = None
        self.is_non_debug = None
        self.is_full_compat = None
        self.report_missing_code_helpers = None
        self.report_missing_trust = None
        self.is_verbose = None
        self.data_composer_verbose = None


states = GlobalState()

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
