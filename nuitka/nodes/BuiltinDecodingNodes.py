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
""" Builtin ord/chr nodes

These are good for optimizations, as they give a very well known result. In the case of
'chr', it's one of 256 strings, and in case of 'ord' it's one of 256 numbers, so these can
answer quite a few questions at compile time.

"""

from .NodeBases import CPythonExpressionBuiltinSingleArgBase

from nuitka.transform.optimizations import BuiltinOptimization


class CPythonExpressionBuiltinOrd( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_ORD"

    builtin_spec = BuiltinOptimization.builtin_ord_spec

    def isKnownToBeIterable( self, count ):
        return False


class CPythonExpressionBuiltinChr( CPythonExpressionBuiltinSingleArgBase ):
    kind = "EXPRESSION_BUILTIN_CHR"

    builtin_spec = BuiltinOptimization.builtin_chr_spec

    def isKnownToBeIterable( self, count ):
        return count is None or count == 1
