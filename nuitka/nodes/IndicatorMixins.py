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
""" Module for node class mixins that indicate runtime determined facts about a node.

These come into play after finalization only. All of the these attributes (and we could
use properties instead) are determined once or from a default and then used like this.

"""

class MarkExceptionBreakContinueIndicator:
    """ Mixin for indication that a break and continue could be real exceptions.

    """

    def __init__( self ):
        self.break_continue_exception = False

    def markAsExceptionBreakContinue( self ):
        self.break_continue_exception = True

    def needsExceptionBreakContinue( self ):
        return self.break_continue_exception

class MarkContainsTryExceptIndicator:
    """ Mixin for indication that a module, class or function contains a try/except.

    """

    def __init__( self ):
        self.try_except_containing = False

    def markAsTryExceptContaining( self ):
        self.try_except_containing = True

    def needsFrameExceptionKeeper( self ):
        return self.try_except_containing

class MarkLocalsDictIndicator:
    def __init__( self ):
        self.needs_locals_dict = False

    def hasLocalsDict( self ):
        return self.needs_locals_dict

    def markAsLocalsDict( self ):
        self.needs_locals_dict = True

class MarkGeneratorIndicator:
    """ Mixin for indication that a function/lambda is a generator.

    """

    def __init__( self ):
        self.is_generator = False

    def markAsGenerator( self ):
        self.is_generator = True

    def isGenerator( self ):
        return self.is_generator


class MarkUnoptimizedFunctionIndicator:
    """ Mixin for indication that a function contains an exec or star import.

        These do not access global variables directly, but check a locals dictionary
        first, because they do.
    """

    def __init__( self ):
        self.unoptimized_locals = False

    def markAsExecContaining( self ):
        self.unoptimized_locals = True

    markAsStarImportContaining = markAsExecContaining

    def isUnoptimized( self ):
        return self.unoptimized_locals
