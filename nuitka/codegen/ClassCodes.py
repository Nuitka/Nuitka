#     Copyright 2015, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Codes for classes.

Most the class specific stuff is solved in re-formulation. Only the selection
of the metaclass remains as specific.
"""


from nuitka.utils import Utils

from .ErrorCodes import getErrorExitCode, getReleaseCode, getReleaseCodes


def _getMetaclassVariableCode(context):
    assert Utils.python_version < 300

    return "GET_STRING_DICT_VALUE( moduledict_%s, (Nuitka_StringObject *)%s )" % (
        context.getModuleCodeName(),
        context.getConstantCode(
            constant = "__metaclass__"
        )
    )


def getSelectMetaclassCode(to_name, metaclass_name, bases_name, emit, context):
    if Utils.python_version < 300:
        assert metaclass_name is None

        args = [
            bases_name,
            _getMetaclassVariableCode(context = context)
        ]
    else:
        args = [
            metaclass_name,
            bases_name
        ]


    emit(
        "%s = SELECT_METACLASS( %s );" % (
            to_name,
            ", ".join(args)
        )
    )

    # Can only fail with Python3.
    if Utils.python_version >= 300:
        getErrorExitCode(
            check_name = to_name,
            emit       = emit,
            context    = context
        )

        getReleaseCodes(
            release_names = args,
            emit          = emit,
            context       = context
        )
    else:
        getReleaseCode(
            release_name = bases_name,
            emit         = emit,
            context      = context
        )

    context.addCleanupTempName(to_name)
