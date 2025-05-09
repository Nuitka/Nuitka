#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Specification record for future flags.

A source reference also implies a specific set of future flags in use by the
parser at that location. Can be different inside a module due to e.g. the
in-lining of "exec" statements with their own future imports, or in-lining of
code from other modules.
"""

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.containers.OrderedSets import OrderedSet
from nuitka.PythonVersions import python_version
from nuitka.utils.InstanceCounters import (
    counted_del,
    counted_init,
    isCountingInstances,
)

# These defaults have changed with Python versions.
_future_division_default = python_version >= 0x300
_future_absolute_import_default = python_version >= 0x300
_future_generator_stop_default = python_version >= 0x370
_future_annotations_default = python_version >= 0x400


class FutureSpec(object):
    # We are using a bunch of flags here, Python decides them and then we add
    # even more modes ourselves, pylint: disable=too-many-instance-attributes

    __slots__ = (
        "future_division",
        "unicode_literals",
        "absolute_import",
        "future_print",
        "barry_bdfl",  # spell-checker: ignore bdfl
        "generator_stop",
        "future_annotations",
        "use_annotations",
    )

    @counted_init
    def __init__(self, use_annotations):
        self.future_division = _future_division_default
        self.unicode_literals = False
        self.absolute_import = _future_absolute_import_default
        self.future_print = False
        self.barry_bdfl = False
        self.generator_stop = _future_generator_stop_default
        self.future_annotations = _future_annotations_default

        # Attaching our special modes here still.
        self.use_annotations = use_annotations

    if isCountingInstances():
        __del__ = counted_del()

    def __repr__(self):
        return "<FutureSpec %s>" % ",".join(self.asFlags())

    def clone(self):
        result = FutureSpec(use_annotations=self.use_annotations)

        result.future_division = self.future_division
        result.unicode_literals = self.unicode_literals
        result.absolute_import = self.absolute_import
        result.future_print = self.future_print
        result.barry_bdfl = self.barry_bdfl
        result.generator_stop = self.generator_stop
        result.future_annotations = result.future_annotations

        return result

    def isFutureDivision(self):
        return self.future_division

    def enableFutureDivision(self):
        self.future_division = True

    def isFuturePrint(self):
        return self.future_print

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

    def enableFutureAnnotations(self):
        self.future_annotations = True

    def shallUseAnnotations(self):
        return self.use_annotations

    def isFutureAnnotations(self):
        return self.future_annotations

    def asFlags(self):
        """Create a list of C identifiers to represent the flag values.

        This is for use in code generation and to restore from
        saved modules.
        """

        result = []

        if python_version < 0x300 and self.future_division:
            result.append("CO_FUTURE_DIVISION")

        if self.unicode_literals:
            result.append("CO_FUTURE_UNICODE_LITERALS")

        if python_version < 0x300 and self.absolute_import:
            result.append("CO_FUTURE_ABSOLUTE_IMPORT")

        if python_version < 0x300 and self.future_print:
            result.append("CO_FUTURE_PRINT_FUNCTION")

        if python_version >= 0x300 and self.barry_bdfl:
            result.append("CO_FUTURE_BARRY_AS_BDFL")

        if 0x350 <= python_version < 0x370 and self.generator_stop:
            result.append("CO_FUTURE_GENERATOR_STOP")

        if python_version >= 0x370 and self.future_annotations:
            result.append("CO_FUTURE_ANNOTATIONS")

        return tuple(result)

    def encode(self):
        # TODO: Maybe asFlags becomes unnecessary.
        return _encodeFlags(self.asFlags())


def fromFlags(flags):
    flags = flags.split(",")
    if "" in flags:
        flags.remove("")

    # TODO: For persistence, that's not very good, but it's actually only using
    # our "no_annotations" flag during building phase, which is completed here,
    # but we might have to add it in the future to XML differently.
    result = FutureSpec(use_annotations=False)

    if "CO_FUTURE_DIVISION" in flags:
        result.enableFutureDivision()

    if "CO_FUTURE_UNICODE_LITERALS" in flags:
        result.enableUnicodeLiterals()

    if "CO_FUTURE_ABSOLUTE_IMPORT" in flags:
        result.enableAbsoluteImport()

    if "CO_FUTURE_PRINT_FUNCTION" in flags:
        result.enableFuturePrint()

    if "CO_FUTURE_BARRY_AS_BDFL" in flags:
        result.enableBarry()

    if "CO_FUTURE_GENERATOR_STOP" in flags:
        result.enableGeneratorStop()

    # Check if we are going to give similar results than what we got.
    assert tuple(result.asFlags()) == tuple(flags), (result, result.asFlags(), flags)

    return result


# Relevance of future flags.
_future_version_specific_flags = OrderedDict(
    (
        ("CO_FUTURE_DIVISION", python_version < 0x300),
        ("CO_FUTURE_UNICODE_LITERALS", True),
        ("CO_FUTURE_PRINT_FUNCTION", python_version < 0x300),
        ("CO_FUTURE_ABSOLUTE_IMPORT", python_version < 0x300),
        ("CO_FUTURE_GENERATOR_STOP", 0x350 <= python_version < 0x370),
        ("CO_FUTURE_ANNOTATIONS", python_version >= 0x370),
        ("CO_FUTURE_BARRY_AS_BDFL", python_version >= 0x300),
    )
)

_future_version_specific_flags = OrderedSet(
    key for (key, value) in _future_version_specific_flags.items() if value
)


def _encodeFlags(flags):
    result = 0
    for bit, flag in enumerate(_future_version_specific_flags):
        if flag in flags:
            result |= 1 << bit
    return result


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
