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

allowed_tags = (
    # New code means new statements with possible variable usages that are
    # not yet bound. Could mean anything.
    "new_code",

    # Added new import.
    "new_import",

    # New statements added.
    "new_statements",

    # New expression added.
    "new_expression",

    # New variable usage pattern introduced.
    "new_variable",

    # TODO: A bit unclear what this it, potentially a changed variable.
    "var_usage",

    # Detected module variable to be read only.
    "read_only_mvar",

    # New builtin function detected.
    "new_builtin",

    # New raise statement detected.
    "new_raise",

    # New constant introduced.
    "new_constant",


)

class TagSet( set ):
    def onSignal( self, signal ):
        if type( signal ) is str:
            signal = signal.split()

        for tag in signal:
            self.add( tag )

    def check( self, tag ):
        return tag in self

    def add( self, tag ):
        assert tag in allowed_tags, tag

        set.add( self, tag )
