#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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
from .GlobalsLocalsCodes import getLoadGlobalsCode, getLoadLocalsCode
from .Helpers import generateExpressionCode, generateExpressionsCode
from .LineNumberCodes import emitLineNumberUpdateCode
from .ModuleCodes import getModuleAccessCode


def generateBuiltinImportCode(to_name, expression, emit, context):
    # We know that 5 expressions are created, pylint: disable=W0632
    module_name, globals_name, locals_name, import_list_name, level_name = \
      generateExpressionsCode(
        expressions = (
            expression.getImportName(),
            expression.getGlobals(),
            expression.getLocals(),
            expression.getFromList(),
            expression.getLevel()
        ),
        names       = (
            "import_modulename",
            "import_globals",
            "import_locals",
            "import_fromlist",
            "import_level"
        ),
        emit        = emit,
        context     = context
    )

    if expression.getGlobals() is None:
        globals_name = context.allocateTempName("import_globals")

        getLoadGlobalsCode(
            to_name = globals_name,
            emit    = emit,
            context = context
        )

    if expression.getLocals() is None:
        provider = expression.getParentVariableProvider()

        if provider.isCompiledPythonModule():
            locals_name = globals_name
        else:
            locals_name = context.allocateTempName("import_locals")

            getLoadLocalsCode(
                to_name  = locals_name,
                provider = provider,
                mode     = provider.getLocalsMode(),
                emit     = emit,
                context  = context
            )

    getBuiltinImportCode(
        to_name          = to_name,
        module_name      = module_name,
        globals_name     = globals_name,
        locals_name      = locals_name,
        import_list_name = import_list_name,
        level_name       = level_name,
        emit             = emit,
        context          = context
    )


def getBuiltinImportCode(to_name, module_name, globals_name, locals_name,
                         import_list_name, level_name, emit, context):

    emitLineNumberUpdateCode(emit, context)

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
            module_name,
            globals_name,
            locals_name,
            import_list_name,
            level_name
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


def generateImportModuleHardCode(to_name, expression, emit, context):
    getImportModuleHardCode(
        to_name     = to_name,
        module_name = expression.getModuleName(),
        import_name = expression.getImportName(),
        needs_check = expression.mayRaiseException(BaseException),
        emit        = emit,
        context     = context
    )


def getImportModuleHardCode(to_name, module_name, import_name, needs_check,
                            emit, context):
    if module_name == "sys":
        emit(
            """%s = PySys_GetObject( (char *)"%s" );""" % (
                to_name,
                import_name
            )
        )
    elif module_name in ("os", "__future__"):
        emit(
             """%s = PyObject_GetAttrString(PyImport_ImportModule("%s"), "%s");""" % (
                to_name,
                module_name,
                import_name
            )
        )
    else:
        assert False, module_name

    if needs_check:
        getErrorExitCode(
            check_name = to_name,
            emit       = emit,
            context    = context
        )


def generateImportModuleCode(to_name, expression, emit, context):
    provider = expression.getParentVariableProvider()

    globals_name = context.allocateTempName("import_globals")

    getLoadGlobalsCode(
        to_name = globals_name,
        emit    = emit,
        context = context
    )

    if provider.isCompiledPythonModule():
        locals_name = globals_name
    else:
        locals_name = context.allocateTempName("import_locals")

        getLoadLocalsCode(
            to_name  = locals_name,
            provider = expression.getParentVariableProvider(),
            mode     = "updated",
            emit     = emit,
            context  = context
        )

    old_source_ref = context.setCurrentSourceCodeReference(expression.getSourceReference())

    getBuiltinImportCode(
        to_name          = to_name,
        module_name      = getConstantCode(
            constant = expression.getModuleName(),
            context  = context
        ),
        globals_name     = globals_name,
        locals_name      = locals_name,
        import_list_name = getConstantCode(
            constant = expression.getImportList(),
            context  = context
        ),
        level_name       = getConstantCode(
            constant = expression.getLevel(),
            context  = context
        ),
        emit             = emit,
        context          = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateImportStarCode(statement, emit, context):
    module_name = context.allocateTempName("star_imported")

    generateImportModuleCode(
        to_name    = module_name,
        expression = statement.getModule(),
        emit       = emit,
        context    = context
    )

    old_source_ref = context.setCurrentSourceCodeReference(statement.getSourceReference())

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

    getReleaseCode(
        release_name = module_name,
        emit         = emit,
        context      = context
    )

    getErrorExitBoolCode(
        condition = "%s == false" % res_name,
        emit      = emit,
        context   = context
    )

    context.setCurrentSourceCodeReference(old_source_ref)


def generateImportNameCode(to_name, expression, emit, context):
    from_arg_name = context.allocateTempName("import_name_from")

    generateExpressionCode(
        to_name    = from_arg_name,
        expression = expression.getModule(),
        emit       = emit,
        context    = context
    )

    emit(
        "%s = IMPORT_NAME( %s, %s );" % (
            to_name,
            from_arg_name,
            getConstantCode(
                constant = expression.getImportName(),
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
