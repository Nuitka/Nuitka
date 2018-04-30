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
""" Code generation for code objects.

Right now only the creation is done here. But more should be added later on.
"""

import os

from nuitka import Options
from nuitka.PythonVersions import python_version


def getCodeObjectsDeclCode(context):
    statements = []

    for _code_object_key, code_identifier in context.getCodeObjects():
        declaration = "static PyCodeObject *%s;" % code_identifier

        statements.append(declaration)

    if context.getOwner().getFullName() == "__main__":
        statements.append('/* For use in "MainProgram.c". */')
        statements.append("PyCodeObject *codeobj_main = NULL;")

    return statements

def getCodeObjectsInitCode(context):
    # There is a bit of details to this, code objects have many flags to deal
    # with, and we are making some optimizations as well as customization to
    # what path should be put there, pylint: disable=too-many-branches

    statements = []

    code_objects = context.getCodeObjects()

    # Create the always identical, but dynamic filename first thing.
    if code_objects:
        context.markAsNeedsModuleFilenameObject()
        filename_code = "module_filename_obj"

    if context.needsModuleFilenameObject():
        module_filename = context.getOwner().getRunTimeFilename()

        # We do not care about release of this object, as code object live
        # forever anyway.
        if Options.getFileReferenceMode() == "frozen" or \
           os.path.isabs(module_filename):
            template = "module_filename_obj = %s;"
        else:
            template = "module_filename_obj = MAKE_RELATIVE_PATH( %s );"

        statements.append(
            template % (
                context.getConstantCode(
                    constant = module_filename
                )
            )
        )

    for code_object_key, code_identifier in code_objects:
        co_flags = []

        # Make sure the filename is always identical.
        assert code_object_key[0] == module_filename

        if code_object_key[6] in ("Module", "Class", "Function"):
            pass
        elif code_object_key[6] == "Generator":
            co_flags.append("CO_GENERATOR")
        elif code_object_key[6] == "Coroutine":
            co_flags.append("CO_COROUTINE")
        elif code_object_key[6] == "Asyncgen":
            co_flags.append("CO_ASYNC_GENERATOR")
        else:
            assert False, code_object_key[6]

        if code_object_key[7]:
            co_flags.append("CO_OPTIMIZED")

        if code_object_key[8]:
            co_flags.append("CO_NEWLOCALS")

        if code_object_key[9]:
            co_flags.append("CO_VARARGS")

        if code_object_key[10]:
            co_flags.append("CO_VARKEYWORDS")

        if not code_object_key[11]:
            co_flags.append("CO_NOFREE")

        co_flags.extend(code_object_key[12])

        if python_version < 300:
            code = "%s = MAKE_CODEOBJ( %s, %s, %d, %s, %d, %s );" % (
                code_identifier,
                filename_code,
                context.getConstantCode(
                    constant = code_object_key[1]
                ),
                code_object_key[2],
                context.getConstantCode(
                    constant = code_object_key[3]
                ),
                code_object_key[4],
                " | ".join(co_flags) or '0',
            )
        else:
            code = "%s = MAKE_CODEOBJ( %s, %s, %d, %s, %d, %d, %s );" % (
                code_identifier,
                filename_code,
                context.getConstantCode(
                    constant = code_object_key[1]
                ),
                code_object_key[2],
                context.getConstantCode(
                    constant = code_object_key[3]
                ),
                code_object_key[4],
                code_object_key[5],
                " | ".join(co_flags) or  '0',
            )

        statements.append(code)

        if context.getOwner().getFullName() == "__main__":
            if code_object_key[1] == "<module>":
                statements.append("codeobj_main = %s;" % code_identifier)
    return statements
