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
""" Finalizations. Last steps directly before code creation is called.

Here the final tasks are executed. Things normally volatile during optimizations can
be computed here, so the code generation can be quick and doesn't have to check it
many times.

"""
from .FinalizeMarkups import FinalizeMarkups
from .FinalizeClosureTaking import FinalizeClosureTaking
from .FinalizeTempVariables import FinalizeTempVariables

# Bug of pylint, it's there but it reports it wrongly, pylint: disable=E0611
from .. import TreeOperations

def prepareCodeGeneration( tree ):
    visitor = FinalizeMarkups()
    TreeOperations.visitTree( tree, visitor )

    visitor = FinalizeClosureTaking()
    TreeOperations.visitTagHaving( tree, visitor, "closure_taker" )

    visitor = FinalizeTempVariables()
    TreeOperations.visitScopes( tree, visitor )
