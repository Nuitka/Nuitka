#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Emission of source code.

Code generation is driven via "emit", which is to receive lines of code and
this is to collect them, providing the emit implementation. Sometimes nested
use of these will occur.

"""

import contextlib

from .Indentation import indented


class SourceCodeCollector(object):
    def __init__(self):
        self.codes = []

    def __call__(self, code):
        self.emit(code)

    def emit(self, code):
        for line in code.split("\n"):
            self.codes.append(line)

    def emitTo(self, emit, level):
        for code in self.codes:
            emit(indented(code, level))

        self.codes = None


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

            for local_declaration in local_declarations:
                emit(indented(local_declaration))

            sub_emit.emitTo(emit, level=4)

            emit("}")
        else:
            sub_emit.emitTo(emit, level=0)

        context.popCleanupScope()


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
