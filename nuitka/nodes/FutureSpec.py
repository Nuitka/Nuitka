#     Copyright 2013, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
""" Specification record for future flags.

A source reference also implies a specific set of future flags in use by the parser at
that location. Can be different inside a module due to e.g. the inlining of exec
statements with their own future imports, or inlining of code from other modules.
"""

from nuitka import Utils

_future_division_default = Utils.python_version >= 300
_future_absolute_import_default = Utils.python_version >= 300

class FutureSpec:
    def __init__( self ):
        self._future_division   = _future_division_default
        self._unicode_literals  = False
        self._absolute_import   = _future_absolute_import_default
        self._future_print      = False
        self._barry_bdfl        = False

    def clone( self ):
        result = FutureSpec()

        result._future_division   = self._future_division
        result._unicode_literals  = self._unicode_literals
        result._absolute_import   = self._absolute_import
        result._future_print      = self._future_print
        result._barry_bdfl        = self._barry_bdfl

        return result

    def isFutureDivision( self ):
        return self._future_division

    def enableFutureDivision( self ):
        self._future_division = True

    def enableFuturePrint( self ):
        self._future_print = True

    def enableUnicodeLiterals( self ):
        self._unicode_literals = True

    def enableAbsoluteImport( self ):
        self._absolute_import = True

    def enableBarry( self ):
        self._barry_bdfl = True

    def isAbsoluteImport( self ):
        return self._absolute_import

    def asFlags( self ):
        result = []

        if self._future_division:
            result.append( "CO_FUTURE_DIVISION" )

        if self._unicode_literals:
            result.append( "CO_FUTURE_UNICODE_LITERALS" )

        if self._absolute_import:
            result.append( "CO_FUTURE_ABSOLUTE_IMPORT" )

        if self._future_print:
            result.append( "CO_FUTURE_PRINT_FUNCTION" )

        if self._barry_bdfl and Utils.python_version >= 300:
            result.append( "CO_FUTURE_BARRY_AS_BDFL" )

        return result
