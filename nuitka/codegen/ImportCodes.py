#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Import related codes.

That is import as expression, and star import.
"""


from .ConstantCodes import getConstantCode
from .ErrorCodes import (
    getErrorExitBoolCode,
    getErrorExitCode,
    getReleaseCode,
    getReleaseCodes
)
from .LineNumberCodes import emitLineNumberUpdateCode
from .ModuleCodes import getModuleAccessCode


def getBuiltinImportCode(to_name, module_name, globals_name, locals_name,
                         import_list_name, level_name, emit, context):

    emitLineNumberUpdateCode(context, emit)

    emit(
        "%s = IMPORT_MODULE( %s, %s, %s, %s, %s );" % (
            to_name,
            module_name,
            globals_name,
            locals_name,
            import_list_name,
            level_name
        )
    )

    getReleaseCodes(
        release_names = (
            module_name, globals_name, locals_name, import_list_name, level_name
        ),
        emit          = emit,
        context       = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)


def getImportModuleHardCode(to_name, module_name, import_name, needs_check,
                            emit, context):
    if module_name == "sys":
        emit(
            """%s = PySys_GetObject( (char *)"%s" );""" % (
                to_name,
                import_name
            )
        )
    elif module_name == "__future__":
        emit(
             """%s = PyObject_GetAttrString(PyImport_ImportModule("__future__"), "%s");""" % (
                to_name,
                import_name
            )
        )


    if needs_check:
        getErrorExitCode(
            check_name = to_name,
            emit       = emit,
            context    = context
        )


def getImportFromStarCode(module_name, emit, context):
    res_name = context.getBoolResName()

    if not context.hasLocalsDict():
        emit(
            "%s = IMPORT_MODULE_STAR( %s, true, %s );" % (
                res_name,
                getModuleAccessCode(
                    context = context
                ),
                module_name
            )
        )
    else:
        emit(
            "%s = IMPORT_MODULE_STAR( locals_dict, false, %s );" % (
                res_name,
                module_name
            )
        )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )

    getReleaseCode(
        release_name = module_name,
        emit         = emit,
        context      = context
    )


def getImportNameCode(to_name, import_name, from_arg_name, emit, context):
    emit(
        "%s = IMPORT_NAME( %s, %s );" % (
            to_name,
            from_arg_name,
            getConstantCode(
                constant = import_name,
                context  = context
            )
        )
    )

    getReleaseCode(
        release_name = from_arg_name,
        emit         = emit,
        context      = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)
