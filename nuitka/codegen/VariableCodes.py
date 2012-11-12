#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
    ModuleVariableIdentifier,
    MaybeModuleVariableIdentifier,
    TempVariableIdentifier,
    TempObjectIdentifier
)

def getVariableHandle( context, variable ):
    assert isinstance( variable, Variables.Variable ), variable

    var_name = variable.getName()

    if variable.isLocalVariable() or variable.isClassVariable():
        return context.getLocalHandle(
            var_name = var_name
        )
    elif variable.isClosureReference():
        return context.getClosureHandle(
            var_name = var_name
        )
    elif variable.isMaybeLocalVariable():
        context.addGlobalVariableNameUsage( var_name )

        assert context.hasLocalsDict(), context

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
    elif variable.isTempVariableReference():
        if not variable.getReferenced().getNeedsFree():
            return TempObjectIdentifier(
                var_name = var_name
            )
        else:
            return TempVariableIdentifier(
                var_name = var_name
            )
    else:
        assert False, variable

def getVariableCode( context, variable ):
    var_identifier = getVariableHandle(
        context  = context,
        variable = variable
    )

    return var_identifier.getCode()
