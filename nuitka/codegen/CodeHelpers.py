#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Helpers for code generation.

This dispatch building of expressions and statements, as well as providing
typical support functions to building parts.

"""

from contextlib import contextmanager

from nuitka.nodes.NodeMetaClasses import NuitkaNodeDesignError
from nuitka.Options import shallTraceExecution
from nuitka.PythonVersions import python_version
from nuitka.Tracing import printError

from .Emission import withSubCollector
from .LabelCodes import getGotoCode, getLabelCode, getStatementTrace

expression_dispatch_dict = {}

_ignore_list_overrides = set(("EXPRESSION_STR_OPERATION_FORMAT",))


def addExpressionDispatchDict(dispatch_dict):
    for key, value in dispatch_dict.items():

        if key in expression_dispatch_dict:
            if key not in _ignore_list_overrides:
                assert False, key

            continue

        expression_dispatch_dict[key] = value


def generateExpressionCode(to_name, expression, emit, context, allow_none=False):
    try:
        _generateExpressionCode(
            to_name=to_name,
            expression=expression,
            emit=emit,
            context=context,
            allow_none=allow_none,
        )
    except Exception:
        printError(
            "Problem with %r at %s"
            % (
                expression,
                ""
                if expression is None
                else expression.getSourceReference().getAsString(),
            )
        )
        raise


def _generateExpressionCode(to_name, expression, emit, context, allow_none=False):
    # This is a dispatching function for every expression.

    if expression is None and allow_none:
        return None

    # Make sure we don't generate code twice for any node, this uncovers bugs
    # where nodes are shared in the tree, which is not allowed.
    assert not hasattr(expression, "code_generated"), expression
    expression.code_generated = True

    if not expression.isExpression():
        printError("No expression %r" % expression)

        expression.dump()
        assert False, expression

    try:
        code_generator = expression_dispatch_dict[expression.kind]
    except KeyError:
        raise NuitkaNodeDesignError(
            expression.__class__.__name__,
            "Need to provide code generation as well",
            expression.kind,
        )

    with context.withCurrentSourceCodeReference(expression.getSourceReference()):
        code_generator(
            to_name=to_name, expression=expression, emit=emit, context=context
        )


def generateExpressionsCode(names, expressions, emit, context):
    assert len(names) == len(expressions)

    result = []
    for name, expression in zip(names, expressions):
        if expression is not None:
            to_name = context.allocateTempName(name)

            generateExpressionCode(
                to_name=to_name, expression=expression, emit=emit, context=context
            )
        else:
            to_name = None

        result.append(to_name)

    return result


def generateChildExpressionsCode(expression, emit, context):
    value_names = []

    for child_name, child_value in expression.getVisitableNodesNamed():
        if type(child_value) is tuple:
            child_names = []

            for child_val in child_value:
                value_name = context.allocateTempName(child_name + "_value")

                generateExpressionCode(
                    to_name=value_name,
                    expression=child_val,
                    emit=emit,
                    context=context,
                )

                child_names.append(value_name)

            value_names.append(tuple(child_names))
        elif child_value is not None:
            # Allocate anyway, so names are aligned.
            value_name = context.allocateTempName(child_name + "_value")

            generateExpressionCode(
                to_name=value_name, expression=child_value, emit=emit, context=context
            )

            value_names.append(value_name)
        else:
            # Allocate anyway, so names are aligned.
            context.skipTempName(child_name + "_value")

            value_names.append(None)

    return value_names


def generateChildExpressionCode(expression, emit, context, child_name=None):
    assert expression is not None

    if child_name is None:
        child_name = expression.getChildName()

    # Allocate anyway, so names are aligned.
    value_name = context.allocateTempName(
        child_name + "_value",
    )

    generateExpressionCode(
        to_name=value_name, expression=expression, emit=emit, context=context
    )

    return value_name


statement_dispatch_dict = {}


def setStatementDispatchDict(dispatch_dict):
    # Using global here, as this is really a singleton, in the form of a module,
    # and this is to break the cyclic dependency it has, pylint: disable=global-statement

    # Please call us only once.
    global statement_dispatch_dict

    assert not statement_dispatch_dict
    statement_dispatch_dict = dispatch_dict


def generateStatementCode(statement, emit, context):
    try:
        statement_dispatch_dict[statement.kind](
            statement=statement, emit=emit, context=context
        )

        # Complain if any temporary was not dealt with yet.
        assert not context.getCleanupTempNames(), context.getCleanupTempNames()
    except Exception:
        printError(
            "Problem with %r at %s"
            % (statement, statement.getSourceReference().getAsString())
        )
        raise


def _generateStatementSequenceCode(statement_sequence, emit, context):
    if statement_sequence is None:
        return

    for statement in statement_sequence.subnode_statements:
        if shallTraceExecution():
            source_ref = statement.getSourceReference()

            statement_repr = repr(statement)
            source_repr = source_ref.getAsString()

            if python_version >= 0x300:
                statement_repr = statement_repr.encode("utf8")
                source_repr = source_repr.encode("utf8")

            emit(getStatementTrace(source_repr, statement_repr))

        # Might contain frame statement sequences as children.
        if statement.isStatementsFrame():
            from .FrameCodes import generateStatementsFrameCode

            generateStatementsFrameCode(
                statement_sequence=statement, emit=emit, context=context
            )
        else:
            with withSubCollector(emit, context) as statement_emit:
                generateStatementCode(
                    statement=statement, emit=statement_emit, context=context
                )


def generateStatementSequenceCode(statement_sequence, emit, context, allow_none=False):
    if allow_none and statement_sequence is None:
        return None

    assert statement_sequence.kind == "STATEMENTS_SEQUENCE", statement_sequence

    _generateStatementSequenceCode(
        statement_sequence=statement_sequence, emit=emit, context=context
    )


def decideConversionCheckNeeded(to_name, expression):
    if to_name.c_type == "nuitka_bool":
        conversion_check = expression.mayRaiseExceptionBool(BaseException)
    else:
        conversion_check = False

    return conversion_check


# TODO: Get rid of the duplication of code with
# "withObjectCodeTemporaryAssignment" by setting on one of them.


@contextmanager
def withObjectCodeTemporaryAssignment2(
    to_name, value_name, needs_conversion_check, emit, context
):
    """Converting to the target type, provide temporary object value name only if necessary."""

    if to_name.c_type == "PyObject *":
        value_name = to_name
    else:
        value_name = context.allocateTempName(value_name)

    yield value_name

    if to_name is not value_name:
        # This is also tasked to release value_name.
        to_name.getCType().emitAssignConversionCode(
            to_name=to_name,
            value_name=value_name,
            needs_check=needs_conversion_check,
            emit=emit,
            context=context,
        )


@contextmanager
def withObjectCodeTemporaryAssignment(to_name, value_name, expression, emit, context):
    """Converting to the target type, provide temporary object value name only if necessary."""

    if to_name.c_type == "PyObject *":
        value_name = to_name
    else:
        value_name = context.allocateTempName(value_name)

    yield value_name

    if to_name is not value_name:
        to_name.getCType().emitAssignConversionCode(
            to_name=to_name,
            value_name=value_name,
            needs_check=decideConversionCheckNeeded(to_name, expression),
            emit=emit,
            context=context,
        )

        from .ErrorCodes import getReleaseCode

        getReleaseCode(value_name, emit, context)


def assignConstantNoneResult(to_name, emit, context):
    # TODO: This is also in SetCode, and should be common for statement only
    # operations that return None in Python, but only in case of non-error
    to_name.getCType().emitAssignmentCodeFromConstant(
        to_name=to_name, constant=None, may_escape=False, emit=emit, context=context
    )

    # This assignment will not necessarily use it, and since it is borrowed,
    # debug mode would otherwise complain.
    if to_name.c_type == "nuitka_void":
        to_name.maybe_unused = True


class HelperCallHandle(object):
    def __init__(
        self,
        helper_name,
        target_type,
        helper_target,
        left_shape,
        helper_left,
        right_shape,
        helper_right,
    ):
        self.helper_name = helper_name
        self.target_type = target_type
        self.helper_target = helper_target
        self.left_shape = left_shape
        self.helper_left = helper_left
        self.right_shape = right_shape
        self.helper_right = helper_right

    def __str__(self):
        return self.helper_name

    def emitHelperCall(self, to_name, arg_names, ref_count, needs_check, emit, context):
        if (
            self.target_type is not None
            and self.target_type.helper_code != self.helper_target.helper_code
        ):
            value_name = context.allocateTempName(
                to_name.code_name + "_" + self.helper_target.helper_code.lower(),
                type_name=self.helper_target.c_type,
                unique=to_name.code_name == "tmp_unused",
            )
        else:
            value_name = to_name

        emit(
            "%s = %s(%s);"
            % (
                value_name,
                self.helper_name,
                ", ".join(
                    "%s%s"
                    % (
                        "&" if count == 0 and "INPLACE" in self.helper_name else "",
                        arg_name,
                    )
                    for count, arg_name in enumerate(arg_names)
                ),
            )
        )

        # TODO: Move helper calling to something separate.
        from .ErrorCodes import (
            getErrorExitCode,
            getReleaseCode,
            getReleaseCodes,
        )

        # TODO: Have a method to indicate these.
        if value_name.getCType().c_type != "bool":
            getErrorExitCode(
                check_name=value_name,
                release_names=arg_names,
                needs_check=needs_check,
                emit=emit,
                context=context,
            )
        else:
            getReleaseCodes(arg_names, emit, context)

        if ref_count:
            context.addCleanupTempName(value_name)

        if (
            self.target_type is not None
            and self.target_type.helper_code != self.helper_target.helper_code
        ):
            if self.target_type.helper_code in ("NBOOL", "NVOID", "CBOOL"):
                self.target_type.emitAssignConversionCode(
                    to_name=to_name,
                    value_name=value_name,
                    needs_check=needs_check,
                    emit=emit,
                    context=context,
                )

                # TODO: Push that release into the emitAssignConversionCode for higher efficiency
                # in code generation, or else error releases are done as well as later release.
                if ref_count:
                    getReleaseCode(value_name, emit, context)
            else:
                assert False, (
                    self.target_type.helper_code,
                    self.helper_target.helper_code,
                )


@contextmanager
def withCleanupFinally(name, release_name, needs_exception, emit, context):

    assert not context.needsCleanup(release_name)

    if needs_exception:
        exception_target = context.allocateLabel("%s_exception" % name)
        old_exception_target = context.setExceptionEscape(exception_target)

    with withSubCollector(emit, context) as guarded_emit:
        yield guarded_emit

    assert not context.needsCleanup(release_name)
    context.addCleanupTempName(release_name)

    if needs_exception:
        noexception_exit = context.allocateLabel("%s_noexception" % name)
        getGotoCode(noexception_exit, emit)

        context.setExceptionEscape(old_exception_target)

        emit("// Exception handling pass through code for %s:" % name)
        getLabelCode(exception_target, emit)

        from .ErrorCodes import getErrorExitReleaseCode

        emit(getErrorExitReleaseCode(context))

        getGotoCode(old_exception_target, emit)

        emit("// Finished with no exception for %s:" % name)
        getLabelCode(noexception_exit, emit)
