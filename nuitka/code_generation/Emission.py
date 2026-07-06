#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Emission of source code.

Code generation is driven via "emit", which is to receive lines of code and
this is to collect them, providing the emit implementation. Sometimes nested
use of these will occur.

"""

import contextlib


def getCodeString(code):
    if type(code) is str:
        return code

    if hasattr(code, "asCode"):
        return code.asCode()

    return str(code)


def _appendCodeString(result, code):
    if type(code) is str:
        result.append(code)
    elif type(code) is SourceCodeTemplateExpansion:
        code.appendToCodeStringFlattened(result)
    elif type(code) is SourceCodeCollector:
        code.appendToCodeStringFlattened(result)
    else:
        result.append(getCodeString(code))


def _joinCodeStrings(codes):
    try:
        return "".join(codes)
    except TypeError:
        result = []

        for code in codes:
            _appendCodeString(result, code)

        return "".join(result)


class SourceCodeTemplateExpansion(object):
    __slots__ = ("template", "values")

    def __init__(self, template, values):
        self.template = template
        self.values = values

    def appendToCodeString(self, result):
        self.template.emit(result.append, self.values)

    def appendToCodeStringFlattened(self, result):
        def append(part):
            _appendCodeString(result, part)

        self.template.emit(append, self.values)

    def asCode(self):
        result = []

        self.appendToCodeString(result)

        return _joinCodeStrings(result)


class SourceCodeCollector(list):
    __slots__ = ("has_template_fragments",)

    def __init__(self):
        list.__init__(self)

        self.has_template_fragments = False

    def __call__(self, code):
        self.append(code)

    emit = __call__

    def emitTemplate(self, template, values):
        self.append(SourceCodeTemplateExpansion(template, values))
        self.has_template_fragments = True

    def reset(self):
        del self[:]
        self.has_template_fragments = False

    def appendToCodeString(self, result):
        for count, code in enumerate(self):
            if count:
                result.append("\n")

            if type(code) is SourceCodeTemplateExpansion:
                code.appendToCodeString(result)
            else:
                result.append(code)

    def appendToCodeStringFlattened(self, result):
        for count, code in enumerate(self):
            if count:
                result.append("\n")

            _appendCodeString(result, code)

    def asCode(self):
        if not self.has_template_fragments:
            try:
                return "\n".join(self)
            except TypeError:
                pass

        result = []

        self.appendToCodeString(result)

        return _joinCodeStrings(result)


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
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
