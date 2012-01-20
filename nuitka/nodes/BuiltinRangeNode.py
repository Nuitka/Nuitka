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
""" Node the calls to the 'range' builtin.

This is a rather complex beast as it has many cases, is difficult to know if it's sizable
enough to compute, and there are complex cases, where the bad result of it can be
predicted still, and these are interesting for warnings.

"""

from .NodeBases import CPythonChildrenHaving, CPythonNodeBase

from .NodeMakingHelpers import getComputationResult

from nuitka.Utils import getPythonVersion

import math

class CPythonExpressionBuiltinRange( CPythonChildrenHaving, CPythonNodeBase ):
    kind = "EXPRESSION_BUILTIN_RANGE"

    named_children = ( "low", "high", "step" )

    def __init__( self, low, high, step, source_ref ):
        CPythonNodeBase.__init__( self, source_ref = source_ref )

        CPythonChildrenHaving.__init__(
            self,
            values = {
                "low"  : low,
                "high" : high,
                "step" : step
            }
        )

    getLow  = CPythonChildrenHaving.childGetter( "low" )
    getHigh = CPythonChildrenHaving.childGetter( "high" )
    getStep = CPythonChildrenHaving.childGetter( "step" )

    def computeNode( self ):
        low  = self.getLow()
        high = self.getHigh()
        step = self.getStep()

        if high is None and step is None:
            if low.isNumberConstant():
                constant = low.getConstant()

                # Avoid warnings before Python 2.7, in Python 2.7 it's an exception.
                if type( constant ) is float and getPythonVersion() < 270:
                    constant = int( constant )

                # Negative values are empty, so don't check against < 0.
                if constant <= 256:
                    return getComputationResult(
                        node        = self,
                        computation = lambda : range( constant ),
                        description = "Range builtin"
                    )
        elif step is None:
            if low.isNumberConstant() and high.isNumberConstant():
                constant1 = low.getConstant()
                constant2 = high.getConstant()

                if type( constant1 ) is float and getPythonVersion() < 270:
                    constant1 = int( constant1 )
                if type( constant2 ) is float and getPythonVersion() < 270:
                    constant2 = int( constant2 )

                if constant2 - constant1 <= 256:
                    return getComputationResult(
                        node        = self,
                        computation = lambda : range( constant1, constant2 ),
                        description = "Range builtin"
                    )
        else:
            if low.isNumberConstant() and high.isNumberConstant() and step.isNumberConstant():
                constant1 = low.getConstant()
                constant2 = high.getConstant()
                constant3 = step.getConstant()

                if type( constant1 ) is float and getPythonVersion() < 270:
                    constant1 = int( constant1 )
                if type( constant2 ) is float and getPythonVersion() < 270:
                    constant2 = int( constant2 )
                if type( constant3 ) is float and getPythonVersion() < 270:
                    constant3 = int( constant3 )

                try:
                    if constant1 < constant2:
                        if constant3 < 0:
                            estimate = 0
                        else:
                            estimate = math.ceil( float( constant2 - constant1 ) / constant3 )
                    else:
                        if constant3 > 0:
                            estimate = 0
                        else:
                            estimate = math.ceil( float( constant2 - constant1 ) / constant3 )
                except (ValueError, TypeError, ZeroDivisionError):
                    estimate = -1

                estimate = round( estimate )

                if estimate <= 256:
                    try:
                        assert len( range( constant1, constant2, constant3 ) ) == estimate, self.getSourceReference()
                    except (ValueError, TypeError, ZeroDivisionError):
                        pass

                    return getComputationResult(
                        node        = self,
                        computation = lambda : range( constant1, constant2, constant3 ),
                        description = "Range builtin"
                    )

        return self, None, None
