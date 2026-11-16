#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Reformulation of subscript and slicing expressions."""

from nuitka.nodes.ConstantRefNodes import ExpressionConstantEllipsisRef
from nuitka.nodes.SliceNodes import (
    ExpressionSliceLookup,
    makeExpressionBuiltinSlice,
)
from nuitka.nodes.SubscriptNodes import ExpressionSubscriptLookup
from nuitka.PythonVersions import python_version

from .ReformulationAssignmentStatements import buildExtSliceNode
from .TreeHelpers import buildNode, getKind


def buildSubscriptNode(provider, node, source_ref):
    assert getKind(node.ctx) == "Load", source_ref

    kind = getKind(node.slice)

    if kind == "Index":
        return ExpressionSubscriptLookup(
            expression=buildNode(provider, node.value, source_ref),
            subscript=buildNode(provider, node.slice.value, source_ref),
            source_ref=source_ref,
        )
    elif kind == "Slice":
        lower = buildNode(
            provider=provider,
            node=node.slice.lower,
            source_ref=source_ref,
            allow_none=True,
        )
        upper = buildNode(
            provider=provider,
            node=node.slice.upper,
            source_ref=source_ref,
            allow_none=True,
        )
        step = buildNode(
            provider=provider,
            node=node.slice.step,
            source_ref=source_ref,
            allow_none=True,
        )

        # For Python3 there is no slicing operation, this is always done
        # with subscript using a slice object. For Python2, it is only done
        # if no "step" is provided.
        use_slice_object = step is not None or python_version >= 0x300

        if use_slice_object:
            return ExpressionSubscriptLookup(
                expression=buildNode(provider, node.value, source_ref),
                subscript=makeExpressionBuiltinSlice(
                    start=lower, stop=upper, step=step, source_ref=source_ref
                ),
                source_ref=source_ref,
            )
        else:
            return ExpressionSliceLookup(
                expression=buildNode(provider, node.value, source_ref),
                lower=lower,
                upper=upper,
                source_ref=source_ref,
            )
    elif kind == "ExtSlice":
        return ExpressionSubscriptLookup(
            expression=buildNode(provider, node.value, source_ref),
            subscript=buildExtSliceNode(provider, node, source_ref),
            source_ref=source_ref,
        )
    elif kind == "Ellipsis":
        return ExpressionSubscriptLookup(
            expression=buildNode(provider, node.value, source_ref),
            subscript=ExpressionConstantEllipsisRef(source_ref=source_ref),
            source_ref=source_ref,
        )
    elif python_version >= 0x390:
        return ExpressionSubscriptLookup(
            expression=buildNode(provider, node.value, source_ref),
            subscript=buildNode(provider, node.slice, source_ref),
            source_ref=source_ref,
        )
    else:
        assert False, kind


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
