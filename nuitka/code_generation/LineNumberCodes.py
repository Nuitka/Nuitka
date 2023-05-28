#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Generate code that updates the source code line.

"""


def getCurrentLineNumberCode(context):
    frame_handle = context.getFrameHandle()

    if frame_handle is None:
        return ""
    else:
        source_ref = context.getCurrentSourceCodeReference()

        if source_ref.isInternal():
            return ""
        else:
            return str(source_ref.getLineNumber())


def getLineNumberUpdateCode(context):
    lineno_value = getCurrentLineNumberCode(context)

    if lineno_value:
        frame_handle = context.getFrameHandle()

        return "%s->m_frame.f_lineno = %s;" % (frame_handle, lineno_value)
    else:
        return ""


def getErrorLineNumberUpdateCode(context):
    (
        _exception_type,
        _exception_value,
        _exception_tb,
        exception_lineno,
    ) = context.variable_storage.getExceptionVariableDescriptions()

    lineno_value = getCurrentLineNumberCode(context)

    if lineno_value:
        return "%s = %s;" % (exception_lineno, lineno_value)
    else:
        return ""


def emitErrorLineNumberUpdateCode(emit, context):
    update_code = getErrorLineNumberUpdateCode(context)

    if update_code:
        emit(update_code)


def emitLineNumberUpdateCode(expression, emit, context):
    # Optional expression.
    if expression is not None:
        context.setCurrentSourceCodeReference(expression.getCompatibleSourceReference())

    code = getLineNumberUpdateCode(context)

    if code:
        emit(code)


def getSetLineNumberCodeRaw(to_name, emit, context):
    assert context.getFrameHandle() is not None

    emit("%s->m_frame.f_lineno = %s;" % (context.getFrameHandle(), to_name))


def getLineNumberCode(to_name, emit, context):
    assert context.getFrameHandle() is not None

    emit("%s = %s->m_frame.f_lineno;" % (to_name, context.getFrameHandle()))
