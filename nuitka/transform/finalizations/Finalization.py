#
#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
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
#     This is to reserve my ability to re-license the code at a later time to
#     the PSF. With this version of Nuitka, using it for a Closed Source and
#     distributing the binary only is not allowed.
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

# Bug of pylint, it's there but it reports it wrongly, pylint: disable=E0611
from .. import TreeOperations

taking_kinds = (
    "EXPRESSION_FUNCTION_BODY",
    "EXPRESSION_CLASS_BODY",
    "EXPRESSION_LIST_CONTRACTION_BODY",
    "EXPRESSION_DICT_CONTRACTION_BODY",
    "EXPRESSION_SET_CONTRACTION_BODY",
    "EXPRESSION_GENERATOR_BODY",
)

def prepareCodeGeneration( tree ):
    visitor = FinalizeMarkups()
    TreeOperations.visitTree( tree, visitor )

    visitor = FinalizeClosureTaking()
    TreeOperations.visitKinds( tree, taking_kinds, visitor )
