#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Low level variable code generation.

"""

from nuitka import Variables

from .Identifiers import ModuleVariableIdentifier, MaybeModuleVariableIdentifier

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
        # TODO: This should depend on no known to hit closure existing
        context.addGlobalVariableNameUsage( var_name )

        assert context.hasLocalsDict()

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
