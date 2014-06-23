#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Yield related codes.

The normal yield, and the Python 3.3 or higher yield from variant.
"""

from .ErrorCodes import getErrorExitCode, getReleaseCode


def getYieldCode(to_name, value_name, in_handler, emit, context):
    emit(
        "%s = %s( generator, %s );" % (
            to_name,
            "YIELD" if not in_handler else "YIELD_IN_HANDLER",
            value_name
              if context.needsCleanup(value_name) else
            "INCREASE_REFCOUNT( %s )" % value_name
        )
    )

    if context.needsCleanup(value_name):
        context.removeCleanupTempName(value_name)

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    # Comes as only borrowed.
    # context.addCleanupTempName(to_name)

def getYieldFromCode(to_name, value_name, in_handler, emit, context):
    emit(
        "%s = %s( generator, %s );" % (
            to_name,
            # TODO: Clarify, if the difference as in getYieldCode is needed.
            "YIELD_FROM" if not in_handler or True else "YIELD_IN_HANDLER",
            value_name
              if context.needsCleanup(value_name) else
            "INCREASE_REFCOUNT( %s )" % value_name
        )
    )

    getReleaseCode(
        release_name = value_name,
        emit         = emit,
        context      = context
    )

    getErrorExitCode(
        check_name = to_name,
        emit       = emit,
        context    = context
    )

    context.addCleanupTempName(to_name)
