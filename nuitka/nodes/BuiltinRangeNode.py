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

from .NodeBases import CPythonExpressionChildrenHavingBase

from .NodeMakingHelpers import getComputationResult

from nuitka.transform.optimizations import BuiltinOptimization

from nuitka.Utils import python_version

import math

class CPythonExpressionBuiltinRange( CPythonExpressionChildrenHavingBase ):
    kind = "EXPRESSION_BUILTIN_RANGE"

    named_children = ( "low", "high", "step" )

    def __init__( self, low, high, step, source_ref ):
        CPythonExpressionChildrenHavingBase.__init__(
            self,
            values = {
                "low"  : low,
                "high" : high,
                "step" : step
            },
            source_ref = source_ref
        )

    getLow  = CPythonExpressionChildrenHavingBase.childGetter( "low" )
    getHigh = CPythonExpressionChildrenHavingBase.childGetter( "high" )
    getStep = CPythonExpressionChildrenHavingBase.childGetter( "step" )

    def _computeNodeNoArgsRange( self ):
        # Intentional to get exception, pylint: disable=W0108
        return getComputationResult(
            node        = self,
            computation = lambda : range(),
            description = "No arg range builtin"
        )

    builtin_spec = BuiltinOptimization.builtin_range_spec

    def computeBuiltinSpec( self, given_values ):
        assert self.builtin_spec is not None, self

        if not self.builtin_spec.isCompileTimeComputable( given_values ):
            return self, None, None

        from .NodeMakingHelpers import getComputationResult

        return getComputationResult(
            node        = self,
            computation = lambda : self.builtin_spec.simulateCall( given_values ),
            description = "Builtin call to %s precomputed." % self.builtin_spec.getName()
        )

    def computeNode( self, constraint_collection ):
        if python_version >= 300:
            return self, None, None

        low  = self.getLow()
        high = self.getHigh()
        step = self.getStep()

        if low is None and high is None and step is None:
            return self._computeNodeNoArgsRange()
        elif high is None and step is None:
            return self.computeBuiltinSpec( ( low, ) )
        elif step is None:
            return self.computeBuiltinSpec( ( low, high ) )
        else:
            return self.computeBuiltinSpec( ( low, high, step ) )

        return self, None, None

    def getIterationLength( self, constraint_collection ):
        low  = self.getLow()
        high = self.getHigh()
        step = self.getStep()

        if low is None and high is None and step is None:
            return 0
        elif high is None and step is None:
            low = low.getIntegerValue( constraint_collection )

            if low is None:
                return None
            else:
                return max( 0, low )
        elif step is None:
            low = low.getIntegerValue( constraint_collection )

            if low is None:
                return None

            high = high.getIntegerValue( constraint_collection )

            if high is None:
                return None

            return max( 0, high - low )
        else:
            low = low.getIntegerValue( constraint_collection )

            if low is None:
                return None

            high = high.getIntegerValue( constraint_collection )

            if high is None:
                return None

            step = step.getIntegerValue( constraint_collection )

            if step is None:
                return None

            # Give up on this, will raise ValueError.
            if step == 0:
                return None

            if low < high:
                if step < 0:
                    estimate = 0
                else:
                    estimate = math.ceil( float( high - low ) / step )
            else:
                if step > 0:
                    estimate = 0
                else:
                    estimate = math.ceil( float( high - low ) / step )

            estimate = round( estimate )

            assert not estimate < 0

            return int( estimate )


    def isKnownToBeIterable( self, count ):
        # We are clearly iterable, but don't know exactly how much. TODO: Analysis could
        # be done to that end.
        return count is None
