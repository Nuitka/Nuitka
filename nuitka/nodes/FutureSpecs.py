#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
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

A source reference also implies a specific set of future flags in use by the
parser at that location. Can be different inside a module due to e.g. the
in-lining of "exec" statements with their own future imports, or in-lining of
code from other modules.
"""

from nuitka.PythonVersions import python_version
from nuitka.utils.InstanceCounters import counted_del, counted_init

# These defaults have changed with Python versions.
_future_division_default = python_version >= 300
_future_absolute_import_default = python_version >= 300
_future_generator_stop_default = python_version >= 360

class FutureSpec:
    @counted_init
    def __init__(self):
        self.future_division  = _future_division_default
        self.unicode_literals = False
        self.absolute_import  = _future_absolute_import_default
        self.future_print     = False
        self.barry_bdfl       = False
        self.generator_stop   = _future_generator_stop_default

    __del__ = counted_del()

    def clone(self):
        result = FutureSpec()

        result.future_division   = self.future_division
        result.unicode_literals  = self.unicode_literals
        result.absolute_import   = self.absolute_import
        result.future_print      = self.future_print
        result.barry_bdfl        = self.barry_bdfl

        return result

    def isFutureDivision(self):
        return self.future_division

    def enableFutureDivision(self):
        self.future_division = True

    def enableFuturePrint(self):
        self.future_print = True

    def enableUnicodeLiterals(self):
        self.unicode_literals = True

    def enableAbsoluteImport(self):
        self.absolute_import = True

    def enableBarry(self):
        self.barry_bdfl = True

    def enableGeneratorStop(self):
        self.generator_stop = True

    def isAbsoluteImport(self):
        return self.absolute_import

    def isGeneratorStop(self):
        return self.generator_stop

    def asFlags(self):
        """ Create a list of C identifiers to represent the flag values.

            This is for use in code generation only.
        """

        result = []

        if self.future_division and python_version < 300:
            result.append("CO_FUTURE_DIVISION")

        if self.unicode_literals:
            result.append("CO_FUTURE_UNICODE_LITERALS")

        if self.absolute_import and python_version < 300:
            result.append("CO_FUTURE_ABSOLUTE_IMPORT")

        if self.future_print and python_version < 300:
            result.append("CO_FUTURE_PRINT_FUNCTION")

        if self.barry_bdfl and python_version >= 300:
            result.append("CO_FUTURE_BARRY_AS_BDFL")

        if self.generator_stop and python_version >= 350:
            result.append("CO_FUTURE_GENERATOR_STOP")

        return tuple(result)
