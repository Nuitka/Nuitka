#
#     Copyright 2010, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an attempt of building an optimizing Python compiler
#     that is compatible and integrates with CPython, but also works on its
#     own.
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

from nuitka import TreeOperations

from logging import warning, debug, info

class OptimizationVisitorBase:
    on_signal = None

    def signalChange( self, tags, source_ref, message ):
        debug( "%s : %s : %s" % ( source_ref.getAsString(), tags, message ) )

        if self.on_signal is not None:
            self.on_signal( tags )

    def execute( self, tree, on_signal = None ):
        self.on_signal = on_signal

        TreeOperations.visitTree(
            tree    = tree,
            visitor = self
        )

def areConstants( expressions ):
    for expression in expressions:
        if not expression.isConstantReference():
            return False
    else:
        return True
