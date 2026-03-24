#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Emission of source code.

Code generation is driven via "emit", which is to receive lines of code and
this is to collect them, providing the emit implementation. Sometimes nested
use of these will occur.

"""

import contextlib


class SourceCodeCollector(list):
    __slots__ = ()

    def __call__(self, code):
        self.append(code)

    emit = __call__


@contextlib.contextmanager
def withSubCollector(emit, context):
    context.pushCleanupScope()

    with context.variable_storage.withLocalStorage():
        sub_emit = SourceCodeCollector()

        # To use the collector and put code in it and C declarations on the context.
        yield sub_emit

        local_declarations = context.variable_storage.makeCLocalDeclarations()

        if local_declarations:
            emit("{")

            emit.extend(local_declarations)
            emit.extend(sub_emit)

            emit("}")
        else:
            emit.extend(sub_emit)

        context.popCleanupScope()


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
