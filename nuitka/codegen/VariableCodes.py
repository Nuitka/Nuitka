#
#     Copyright 2011, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
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

from .Identifiers import ModuleVariableIdentifier

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

        return context.getMaybeLocalHandle(
            var_name = var_name
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
