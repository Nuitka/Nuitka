#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
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
    ClosureVariableIdentifier,
    ModuleVariableIdentifier,
    LocalVariableIdentifier,
    TempVariableIdentifier,
    TempObjectIdentifier,
    encodeNonAscii
)

from .ConstantCodes import getConstantCode

def getVariableHandle( context, variable ):
    assert isinstance( variable, Variables.Variable ), variable

    var_name = variable.getName()

    if variable.isLocalVariable() or variable.isClassVariable():
        return LocalVariableIdentifier(
            var_name     = var_name,
            from_context = context.getFunction().isGenerator()
        )
    elif variable.isTempVariableReference():
        if not variable.getOwner().isStatementTempBlock():
            variable = variable.getReferenced()

        if not variable.getReferenced().getNeedsFree():
            return TempObjectIdentifier(
                var_name = var_name
            )
        else:
            return TempVariableIdentifier(
                var_name = var_name
            )
    elif variable.isClosureReference():
        function = context.getFunction()

        # Context access is variant depending on if that's a created function or
        # not. For generators, they even share closure variables in the common
        # context.
        if function.needsCreation():
            if function.isGenerator():
                from_context = "_python_context->common_context->"
            else:
                from_context = "_python_context->"
        else:
            if function.isGenerator():
                from_context = "_python_context->"
            else:
                from_context = ""

        return ClosureVariableIdentifier(
            var_name     = var_name,
            from_context = from_context
        )
    elif variable.isMaybeLocalVariable():
        context.addGlobalVariableNameUsage( var_name )

        assert context.getFunction().hasLocalsDict(), context

        return MaybeModuleVariableIdentifier(
            var_name         = var_name,
            module_code_name = context.getModuleCodeName()
        )
    elif variable.isModuleVariable():
        context.addGlobalVariableNameUsage(
            var_name = var_name
        )

        return ModuleVariableIdentifier(
            var_name         = var_name,
            module_code_name = context.getModuleCodeName()
        )
    else:
        assert False, variable

def getVariableCode( context, variable ):
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

    if not in_context:
        result += "_"

    result += encodeNonAscii( variable.getCodeName() )

    if not in_context:
        if variable.isTempVariable():
            if init_from is None:
                result += " = " + variable.getDeclarationInitValueCode()
            elif not variable.getNeedsFree():
                result += " = %s" % init_from.getCodeTemporaryRef()
            else:
                result += "( %s )" % init_from.getCodeExportRef()
        else:
            result += "( "

            result += "%s" % getConstantCode(
                context  = context,
                constant = store_name
            )

            if init_from is not None:
                if context.hasLocalsDict():
                    if init_from.getCheapRefCount() == 0:
                        result += ", %s" % init_from.getCodeTemporaryRef()
                    else:
                        result += ", %s" % init_from.getCodeExportRef()

                        if not variable.isParameterVariable():
                            result += ", true"
                else:
                    result += ", %s" % init_from.getCodeExportRef()

            result += " )"

    result += ";"

    return result
