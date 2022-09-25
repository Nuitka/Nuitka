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
""" Nodes for all things "ctypes" stdlib module.

"""

from nuitka.specs.BuiltinParameterSpecs import (
    BuiltinParameterSpec,
    extractBuiltinArgs,
)

from .ExpressionBases import ExpressionChildrenHavingBase
from .ImportHardNodes import ExpressionImportModuleNameHardExistsSpecificBase

# spell-checker: ignore lasterror,winmode

if str is bytes:
    ctypes_cdll_args = (
        "name",
        "mode",
        "handle",
        "use_errno",
        "use_lasterror",
        "winmode",
    )
else:
    ctypes_cdll_args = ("name", "mode", "handle", "use_errno", "use_lasterror")


ctypes_cdll_spec = BuiltinParameterSpec(
    "ctypes.CDLL", ctypes_cdll_args, default_count=len(ctypes_cdll_args) - 1
)


class ExpressionCtypesCdllRef(ExpressionImportModuleNameHardExistsSpecificBase):
    """Function reference ctypes.CDLL"""

    kind = "EXPRESSION_CTYPES_CDLL_REF"

    def __init__(self, source_ref):
        ExpressionImportModuleNameHardExistsSpecificBase.__init__(
            self,
            module_name="ctypes",
            import_name="CDLL",
            module_guaranteed=True,
            source_ref=source_ref,
        )

    def computeExpressionCall(self, call_node, call_args, call_kw, trace_collection):
        # Anything may happen. On next pass, if replaced, we might be better
        # but not now.
        trace_collection.onExceptionRaiseExit(BaseException)

        result = extractBuiltinArgs(
            node=call_node,
            builtin_class=ExpressionCtypesCdllCall,
            builtin_spec=ctypes_cdll_spec,
        )

        return result, "new_expression", "Call to 'ctypes.CDLL' recognized."


class ExpressionCtypesCdllCall(ExpressionChildrenHavingBase):
    """Function reference ctypes.CDLL"""

    kind = "EXPRESSION_CTYPES_CDLL_CALL"

    named_children = ctypes_cdll_args

    spec = ctypes_cdll_spec

    # Lazy in making winmode Python2 only with same code.
    def __init__(
        self,
        name,
        mode,
        handle,
        use_errno,
        use_lasterror,
        winmode=None,
        source_ref=None,
    ):
        values = {
            "name": name,
            "mode": mode,
            "handle": handle,
            "use_errno": use_errno,
            "use_lasterror": use_lasterror,
        }

        if "winmode" in ctypes_cdll_args:
            values["winmode"] = winmode

        ExpressionChildrenHavingBase.__init__(
            self, values=values, source_ref=source_ref
        )

    def computeExpression(self, trace_collection):
        trace_collection.onExceptionRaiseExit(BaseException)

        return self, None, None
