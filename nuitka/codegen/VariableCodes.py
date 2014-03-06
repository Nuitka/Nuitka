#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Low level variable code generation.

"""

from nuitka import Variables

from .Identifiers import (
    MaybeModuleVariableIdentifier,
    ModuleVariableIdentifier,
    TempObjectIdentifier,
    NameIdentifier
)

from .ConstantCodes import getConstantCode

from .Indentation import (
    getBlockCode,
)

def _getContextAccess(context, force_closure = False):
    # Context access is variant depending on if that's a created function or
    # not. For generators, they even share closure variables in the common
    # context.
    if context.isPythonModule():
        return ""
    else:
        function = context.getFunction()

        if function.needsCreation():
            if function.isGenerator():
                if force_closure:
                    return "_python_context->common_context->"
                else:
                    return "_python_context->"
            else:
                if force_closure:
                    return "_python_context->"
                else:
                    return ""
        else:
            if function.isGenerator():
                return "_python_context->"
            else:
                return ""


def getVariableHandle(context, variable):
    assert isinstance( variable, Variables.Variable ), variable

    var_name = variable.getName()

    if variable.isParameterVariable() or \
       variable.isLocalVariable() or \
       variable.isClassVariable() or \
       ( variable.isClosureReference() and not variable.isTempVariableReference() ):
        from_context = _getContextAccess(
            context       = context,
            force_closure = variable.isClosureReference()
        )

        code = from_context + variable.getCodeName()

        if variable.isParameterVariable():
            hint = "parameter"
        elif variable.isClassVariable():
            hint = "classvar"
        elif variable.isClosureReference():
            hint = "closure"
        else:
            hint = "localvar"

        return NameIdentifier(
            hint      = hint,
            name      = var_name,
            code      = code,
            ref_count = 0
        )
    elif variable.isTempVariableReference() and \
         variable.isClosureReference() and \
         variable.isShared( True ):
        return TempVariableIdentifier(
            var_name     = var_name,
            from_context = _getContextAccess(
                context       = context,
                force_closure = True
            )
        )
    elif variable.isTempVariableReference():
        variable = variable.getReferenced()

        if variable.isTempVariableReference():
            variable = variable.getReferenced()

        if variable.needsLateDeclaration():
            from_context = ""
        else:
            from_context = _getContextAccess(
                context,
                variable.isShared( True )
            )

        if variable.isShared( True ):
            return NameIdentifier(
                hint      = "tempvar",
                name      = var_name,
                code      = from_context + variable.getCodeName(),
                ref_count = 0
            )
        elif not variable.getNeedsFree():
            return TempObjectIdentifier(
                var_name     = var_name,
                code         = from_context + variable.getCodeName()
            )
        else:
            return NameIdentifier(
                hint      = "tempvar",
                name      = var_name,
                code      = from_context + variable.getCodeName(),
                ref_count = 0
            )
    elif variable.isMaybeLocalVariable():
        assert context.getFunction().hasLocalsDict(), context

        return MaybeModuleVariableIdentifier(
            var_name      = var_name,
            var_code_name = getConstantCode(
                context  = context,
                constant = var_name
            )
        )
    elif variable.isModuleVariable():
        return ModuleVariableIdentifier(
            var_name      = var_name,
            var_code_name = getConstantCode(
                context  = context,
                constant = var_name
            )
        )
    else:
        assert False, variable

def getVariableCode(context, variable):
    var_identifier = getVariableHandle(
        context  = context,
        variable = variable
    )

    return var_identifier.getCode()

def getLocalVariableInitCode( context, variable, init_from = None,
                              in_context = False ):
    # This has many cases to deal with, so there need to be a lot of branches.
    # pylint: disable=R0912

    assert not variable.isModuleVariable()

    assert init_from is None or hasattr( init_from, "getCodeTemporaryRef" )

    result = variable.getDeclarationTypeCode( in_context )

    # For pointer types, we don't have to separate with spaces.
    if not result.endswith( "*" ):
        result += " "

    store_name = variable.getMangledName()

    result += variable.getCodeName()

    if not in_context:
        if variable.isTempVariable():
            assert init_from is None

            if variable.isShared( True ):
                result += "( NULL )"
            elif not variable.getNeedsFree():
                result += " = " + variable.getDeclarationInitValueCode()
        else:
            result += "( "

            result += "%s" % getConstantCode(
                context  = context,
                constant = store_name
            )

            if init_from is not None:
                result += ", %s" % init_from.getCodeExportRef()

            result += " )"

    result += ";"

    return result

def getVariableAssignmentCode(context, variable, identifier):
    assert isinstance( variable, Variables.Variable ), variable

    # This ought to be impossible to happen, as an assignment to an overflow
    # variable would have made it a local one.
    assert not variable.isMaybeLocalVariable()

    if variable.isTempVariableReference():
        referenced = variable.getReferenced()

        if referenced.needsLateDeclaration() and not referenced.isDeclared():
            referenced.markAsDeclared()

            variable_code = getVariableCode(
                variable = variable,
                context  = context
            )

            local_inits = context.getTempKeeperDecl()

            if referenced.getNeedsFree():
                prefix = "PyObject *_%s;" % variable_code

                if local_inits:
                    result = "_%s = %s;" % (
                        variable_code,
                        identifier.getCodeExportRef()
                    )

                    result = getBlockCode(
                        local_inits + result.split( "\n" )
                    )

                    postfix = "%s %s( _%s );" % (
                        referenced.getDeclarationTypeCode( False ),
                        variable_code,
                        variable_code
                    )

                    return prefix + "\n" + result + "\n" + postfix
                else:
                    return "%s %s( %s );" % (
                        referenced.getDeclarationTypeCode( False ),
                        variable_code,
                        identifier.getCodeExportRef()
                    )
            else:
                if local_inits:
                    prefix = "PyObject *%s;" % variable_code

                    result = "%s = %s;" % (
                        variable_code,
                        identifier.getCodeTemporaryRef()
                    )

                    result = getBlockCode(
                        local_inits + result.split( "\n" )
                    )

                    return prefix + "\n" + result
                else:
                    return "PyObject *%s = %s;" % (
                        variable_code,
                        identifier.getCodeTemporaryRef()
                    )

        if not referenced.isShared( True ) and not referenced.getNeedsFree():
            # So won't get a reference, and take none, or else it may get lost,
            # which we don't want to happen.

            # This must be true, otherwise the needs no free statement was made
            # in error.
            assert identifier.getCheapRefCount() == 0

            left_side = getVariableCode(
                variable = variable,
                context  = context
            )

            assert "(" not in left_side

            return "%s = %s;" % (
                left_side,
                identifier.getCodeTemporaryRef()
            )

    if identifier.getCheapRefCount() == 0:
        identifier_code = identifier.getCodeTemporaryRef()
        assign_code = "0"
    else:
        identifier_code = identifier.getCodeExportRef()
        assign_code = "1"

    if variable.isModuleVariable():
        return "UPDATE_STRING_DICT%s( moduledict_%s, (Nuitka_StringObject *)%s, %s );" % (
            assign_code,
            context.getModuleCodeName(),
            getConstantCode(
                constant = variable.getName(),
                context  = context
            ),
            identifier_code
        )

    return "%s.assign%s( %s );" % (
        getVariableCode(
            variable = variable,
            context  = context
        ),
        assign_code,
        identifier_code
    )

def getVariableDelCode(context, tolerant, variable):
    assert isinstance( variable, Variables.Variable ), variable

    if variable.isModuleVariable():
        return "DEL_MODULE_VALUE( %s, %s );" % (
            getConstantCode(
                context  = context,
                constant = variable.getName()
            ),
            "true" if tolerant else "false"
        )
    else:
        if variable.isTempVariableReference():
            if not variable.isShared( True ) and \
               not variable.getReferenced().getNeedsFree():
                return "%s = NULL;" % (
                    getVariableCode(
                        variable = variable,
                        context  = context
                    )
                )

        return "%s.del( %s );" % (
            getVariableCode(
                variable = variable,
                context  = context
            ),
            "true" if tolerant else "false"
        )
