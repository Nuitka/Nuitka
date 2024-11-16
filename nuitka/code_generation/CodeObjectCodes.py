#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Code generation for code objects.

Right now only the creation is done here. But more should be added later on.
"""

import os

from nuitka.__past__ import unicode
from nuitka.Options import getFileReferenceMode
from nuitka.PythonVersions import python_version


def getCodeObjectsDeclCode(context):
    statements = []

    for _code_object_key, code_identifier in context.getCodeObjects():
        declaration = "static PyCodeObject *%s;" % code_identifier

        statements.append(declaration)

    if context.getOwner().getFullName() == "__main__":
        statements.append('/* For use in "MainProgram.c". */')
        statements.append("PyCodeObject *code_objects_main = NULL;")

    return statements


def _getMakeCodeObjectArgs(code_object_handle, context):
    """Code objects have many flags for creation.

    This is also version dependent, but we hide this behind macros
    that ignore some arguments.
    """

    co_flags = []

    if code_object_handle.co_kind in ("Module", "Class", "Function"):
        pass
    elif code_object_handle.co_kind == "Generator":
        co_flags.append("CO_GENERATOR")
    elif code_object_handle.co_kind == "Coroutine":
        co_flags.append("CO_COROUTINE")
    elif code_object_handle.co_kind == "Asyncgen":
        co_flags.append("CO_ASYNC_GENERATOR")
    else:
        assert False, code_object_handle.co_kind

    if code_object_handle.is_optimized:
        co_flags.append("CO_OPTIMIZED")

    if code_object_handle.co_new_locals:
        co_flags.append("CO_NEWLOCALS")

    if code_object_handle.co_has_starlist:
        co_flags.append("CO_VARARGS")

    if code_object_handle.co_has_stardict:
        co_flags.append("CO_VARKEYWORDS")

    if not code_object_handle.co_freevars and python_version < 0x3B0:
        co_flags.append("CO_NOFREE")

    co_flags.extend(code_object_handle.future_flags)

    return (
        code_object_handle.line_number,
        " | ".join(co_flags) or "0",
        context.getConstantCode(constant=code_object_handle.co_name),
        context.getConstantCode(constant=code_object_handle.co_qualname),
        (
            context.getConstantCode(constant=code_object_handle.co_varnames)
            if code_object_handle.co_varnames
            else "NULL"
        ),
        (
            context.getConstantCode(constant=code_object_handle.co_freevars)
            if code_object_handle.co_freevars
            else "NULL"
        ),
        code_object_handle.co_argcount,
        code_object_handle.co_kwonlyargcount,
        code_object_handle.co_posonlyargcount,
    )


def getCodeObjectsInitCode(context):
    # There is a bit of details to this, and we are making some optimizations as
    # well as customization to what path should be put there.

    statements = []

    code_objects = context.getCodeObjects()

    # Create the always identical, but dynamic filename first thing.
    module_filename = context.getOwner().getRunTimeFilename()

    # We do not care about release of this object, as code object live
    # forever anyway.
    if getFileReferenceMode() == "frozen" or os.path.isabs(module_filename):
        template = "module_filename_obj = %s; CHECK_OBJECT(module_filename_obj);"
    else:
        template = "module_filename_obj = MAKE_RELATIVE_PATH(%s); CHECK_OBJECT(module_filename_obj);"

    if str is bytes and type(module_filename) is unicode:
        module_filename = module_filename.encode("utf8")

    # The code object will not work from any other type, cannot be e.g. unicode.
    assert type(module_filename) is str, (type(module_filename), module_filename)

    statements.append(template % (context.getConstantCode(constant=module_filename)))

    for code_object_key, code_identifier in code_objects:
        # Make sure the filename is always identical.
        assert code_object_key.co_filename == module_filename, code_object_key

        args = (
            code_identifier,
            ", ".join(str(s) for s in _getMakeCodeObjectArgs(code_object_key, context)),
        )

        code = "%s = MAKE_CODE_OBJECT(module_filename_obj, %s);" % args

        statements.append(code)

        if context.getOwner().getFullName() == "__main__":
            if code_object_key[1] == "<module>":
                statements.append("code_objects_main = %s;" % code_identifier)

    return statements


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
