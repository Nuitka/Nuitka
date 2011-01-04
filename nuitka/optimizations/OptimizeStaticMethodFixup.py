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
""" Delete the staticmethod decorator from __new__ methods if provided.

CPython made these optional, and applies them to every __new__. Our later code will be
confused if it encounters a decorator to what it already automatically decorated.

TODO: Consider turning this into something adding it for improved consistency.
"""

from OptimizeBase import OptimizationVisitorBase

class FixupNewStaticMethodVisitor( OptimizationVisitorBase ):
    def __call__( self, node ):
        if node.isFunctionReference() and node.getName() == "__new__":
            decorators = node.getDecorators()

            if len( decorators ) == 1 and decorators[0].isVariableReference():
                if decorators[0].getVariable().getName() == "staticmethod":
                    # Reset the decorators. This does not attempt to deal with
                    # multiple of them being present.
                    node.setDecorators( () )

                    assert not node.getDecorators()
