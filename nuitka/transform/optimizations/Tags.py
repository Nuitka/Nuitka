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
""" Tags and set of it.

Used by optimization to keep track of the current state of optimization, these tags
trigger the execution of optimization steps, which in turn may emit these tags to execute
other steps.

"""


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

    # New module recursed to.
    "new_module",

)

class TagSet( set ):
    def onSignal( self, signal ):
        if type( signal ) is str:
            signal = signal.split()

        for tag in signal:
            self.add( tag )

    def check( self, tags ):
        for tag in tags.split():
            assert tag in allowed_tags, tag

            if tag in self:
                return True
        else:
            return False

    def add( self, tag ):
        assert tag in allowed_tags, tag

        set.add( self, tag )
