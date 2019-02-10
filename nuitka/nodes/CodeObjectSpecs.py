#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Code object specifications.

For code objects that will be attached to module, function, and generator
objects, as well as tracebacks. They might be shared.

"""

from nuitka.utils.InstanceCounters import counted_del, counted_init


class CodeObjectSpec(object):
    # One attribute for each code object aspect, and even flags,
    # pylint: disable=too-many-arguments,too-many-instance-attributes
    __slots__ = (
        "co_name",
        "co_kind",
        "co_varnames",
        "co_argcount",
        "co_kwonlyargcount",
        "co_has_starlist",
        "co_has_stardict",
        "filename",
        "line_number",
        "future_spec",
        "new_locals",
        "has_closure",
        "is_optimized",
    )

    @counted_init
    def __init__(
        self,
        co_name,
        co_kind,
        co_varnames,
        co_argcount,
        co_kwonlyargcount,
        co_has_starlist,
        co_has_stardict,
        co_filename,
        co_lineno,
        future_spec,
        co_new_locals=None,
        co_has_closure=None,
        co_is_optimized=None,
    ):

        self.co_name = co_name
        self.co_kind = co_kind

        self.future_spec = future_spec
        assert future_spec

        # Strings happens from XML parsing, make sure to convert them.
        if type(co_varnames) is str:
            if co_varnames == "":
                co_varnames = ()
            else:
                co_varnames = co_varnames.split(",")

        if type(co_has_starlist) is not bool:
            co_has_starlist = co_has_starlist != "False"
        if type(co_has_stardict) is not bool:
            co_has_stardict = co_has_stardict != "False"

        self.co_varnames = tuple(co_varnames)

        self.co_argcount = int(co_argcount)
        self.co_kwonlyargcount = int(co_kwonlyargcount)

        self.co_has_starlist = co_has_starlist
        self.co_has_stardict = co_has_stardict

        self.filename = co_filename
        self.line_number = int(co_lineno)

        if type(co_has_starlist) is not bool:
            co_new_locals = co_new_locals != "False"
        if type(co_has_starlist) is not bool:
            co_has_closure = co_has_closure != "False"
        if type(co_has_starlist) is not bool:
            co_is_optimized = co_is_optimized != "False"

        self.new_locals = co_new_locals
        self.has_closure = co_has_closure
        self.is_optimized = co_is_optimized

    __del__ = counted_del()

    def __repr__(self):
        return (
            """\
<CodeObjectSpec %(co_kind)s '%(co_name)s' with %(co_varnames)r>"""
            % self.getDetails()
        )

    def getDetails(self):
        return {
            "co_name": self.co_name,
            "co_kind": self.co_kind,
            "co_varnames": ",".join(self.co_varnames),
            "co_argcount": self.co_argcount,
            "co_kwonlyargcount": self.co_kwonlyargcount,
            "co_has_starlist": self.co_has_starlist,
            "co_has_stardict": self.co_has_stardict,
            "co_filename": self.filename,
            "co_lineno": self.line_number,
            "co_new_locals": self.new_locals,
            "co_has_closure": self.has_closure,
            "co_is_optimized": self.is_optimized,
            "code_flags": ",".join(self.future_spec.asFlags()),
        }

    def getCodeObjectKind(self):
        return self.co_kind

    def updateLocalNames(self, local_names):
        """ Add detected local variables after closure has been decided.

        """
        self.co_varnames += tuple(
            local_name
            for local_name in local_names
            if local_name not in self.co_varnames
        )

    def setFlagIsOptimizedValue(self, value):
        self.is_optimized = value

    def getFlagIsOptimizedValue(self):
        return self.is_optimized

    def setFlagNewLocalsValue(self, value):
        self.new_locals = value

    def getFlagNewLocalsValue(self):
        return self.new_locals

    def setFlagHasClosureValue(self, value):
        self.has_closure = value

    def getFlagHasClosureValue(self):
        return self.has_closure

    def getFutureSpec(self):
        return self.future_spec

    def getVarNames(self):
        return self.co_varnames

    def getArgumentCount(self):
        return self.co_argcount

    def getKwOnlyParameterCount(self):
        return self.co_kwonlyargcount

    def getCodeObjectName(self):
        return self.co_name

    def hasStarListArg(self):
        return self.co_has_starlist

    def hasStarDictArg(self):
        return self.co_has_stardict

    def getFilename(self):
        return self.filename

    def getLineNumber(self):
        return self.line_number
