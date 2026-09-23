#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Code object specifications.

For code objects that will be attached to module, function, and generator
objects, as well as tracebacks. They might be shared.

"""

from nuitka.PythonVersions import python_version
from nuitka.utils.Hashing import getStringHash
from nuitka.utils.InstanceCounters import (
    counted_del,
    counted_init,
    isCountingInstances,
)


class CodeObjectSpec(object):
    # One attribute for each code object aspect, and even flags,
    # pylint: disable=too-many-arguments,too-many-instance-attributes
    __slots__ = (
        "co_name",
        "co_qualname",
        "co_kind",
        "co_varnames",
        "co_argcount",
        "co_freevars",
        "co_posonlyargcount",
        "co_kwonlyargcount",
        "co_has_starlist",
        "co_has_stardict",
        "filename",
        "line_number",
        "future_spec",
        "new_locals",
        "is_optimized",
    )

    @counted_init
    def __init__(
        self,
        co_name,
        co_qualname,
        co_kind,
        co_varnames,
        co_freevars,
        co_argcount,
        co_posonlyargcount,
        co_kwonlyargcount,
        co_has_starlist,
        co_has_stardict,
        co_filename,
        co_lineno,
        future_spec,
        co_new_locals=None,
        co_is_optimized=None,
    ):
        # pylint: disable=I0021,too-many-locals

        self.co_name = co_name
        self.co_qualname = co_qualname
        self.co_kind = co_kind

        self.future_spec = future_spec
        assert future_spec

        # Strings happens from XML parsing, make sure to convert them.
        if type(co_varnames) is str:
            if co_varnames == "":
                co_varnames = ()
            else:
                co_varnames = co_varnames.split(",")

        if type(co_freevars) is str:
            if co_freevars == "":
                co_freevars = ()
            else:
                co_freevars = co_freevars.split(",")

        if type(co_has_starlist) is not bool:
            co_has_starlist = co_has_starlist != "False"
        if type(co_has_stardict) is not bool:
            co_has_stardict = co_has_stardict != "False"

        self.co_varnames = tuple(co_varnames)
        self.co_freevars = tuple(co_freevars)

        self.co_argcount = int(co_argcount)

        self.co_posonlyargcount = int(co_posonlyargcount)
        self.co_kwonlyargcount = int(co_kwonlyargcount)

        self.co_has_starlist = co_has_starlist
        self.co_has_stardict = co_has_stardict

        self.filename = co_filename
        self.line_number = int(co_lineno)

        if type(co_new_locals) is not bool:
            co_new_locals = co_new_locals != "False"
        if type(co_is_optimized) is not bool:
            co_is_optimized = co_is_optimized != "False"

        self.new_locals = co_new_locals
        self.is_optimized = co_is_optimized

    if isCountingInstances():
        __del__ = counted_del()

    def __repr__(self):
        return (
            """\
<CodeObjectSpec %(co_kind)s '%(co_name)s' with var_names %(co_varnames)r>"""
            % self.getDetails()
        )

    def getDetails(self):
        return {
            "co_name": self.co_name,
            "co_kind": self.co_kind,
            "co_varnames": ",".join(self.co_varnames),
            "co_freevars": ",".join(self.co_freevars),
            "co_argcount": self.co_argcount,
            "co_posonlyargcount": self.co_posonlyargcount,
            "co_kwonlyargcount": self.co_kwonlyargcount,
            "co_has_starlist": self.co_has_starlist,
            "co_has_stardict": self.co_has_stardict,
            "co_filename": self.filename,
            "co_lineno": self.line_number,
            "co_new_locals": self.new_locals,
            "co_is_optimized": self.is_optimized,
            "code_flags": ",".join(self.future_spec.asFlags()),
        }

    def getHash(self):
        return getStringHash(
            "|".join(
                "%s=%s" % (key, value)
                for key, value in sorted(self.getDetails().items())
            )
        )

    def getCodeObjectKind(self):
        return self.co_kind

    # Follow CPython naming, spell-checker: ignore freevar
    def updateLocalNames(self, local_names, freevar_names):
        """Move detected local variables after closure has been decided."""

        self.co_varnames += tuple(
            local_name
            for local_name in local_names
            if local_name not in self.co_varnames
            # TODO: This is actually a bug, but we have a hard time without it to know
            # frame locals easily. We use this in compiled function run time, that all
            # variables, including closure variables are found there. This would have to
            # be cleaned up, for potentially little gain.
            # if local_name not in freevar_names
        )

        self.co_freevars = tuple(freevar_names)

    def removeFreeVarname(self, freevar_name):
        self.co_freevars = tuple(
            var_name for var_name in self.co_freevars if var_name != freevar_name
        )

    def setFlagIsOptimizedValue(self, value):
        self.is_optimized = value

    def getFlagIsOptimizedValue(self):
        return self.is_optimized

    def setFlagNewLocalsValue(self, value):
        self.new_locals = value

    def getFlagNewLocalsValue(self):
        return self.new_locals

    def getFutureSpec(self):
        return self.future_spec

    def getVarNames(self):
        return self.co_varnames

    def getFreeVarNames(self):
        return self.co_freevars

    def getArgumentCount(self):
        return self.co_argcount

    def getPosOnlyParameterCount(self):
        return self.co_posonlyargcount

    def getKwOnlyParameterCount(self):
        return self.co_kwonlyargcount

    def getCodeObjectName(self):
        return self.co_name

    def getCodeObjectQualname(self):
        return self.co_qualname

    def hasStarListArg(self):
        return self.co_has_starlist

    def hasStarDictArg(self):
        return self.co_has_stardict

    def getFilename(self):
        return self.filename

    def getLineNumber(self):
        return self.line_number

    @classmethod
    def fromXML(cls, **args):
        """Reconstruct from XML details.

        Args:
            args: the code object details as needed by the constructor.

        Returns:
            Instance of the code object spec class.
        """
        return cls(**args)


class CodeObjectSpecModule(CodeObjectSpec):
    """Code object specification of a module frame.

    Notes:
        Module code objects have fixed values for all details except the
        filename and future spec, even the line number is always 1. The
        module name is only used for display purposes, not for the code
        object itself.
    """

    __slots__ = ("module_name",)

    def __init__(self, module_name, co_filename, future_spec):
        self.module_name = module_name

        CodeObjectSpec.__init__(
            self,
            co_name="<module>",
            co_qualname="<module>",
            co_kind="Module",
            co_varnames=(),
            co_freevars=(),
            co_argcount=0,
            co_posonlyargcount=0,
            co_kwonlyargcount=0,
            co_has_starlist=False,
            co_has_stardict=False,
            co_filename=co_filename,
            co_lineno=1,
            future_spec=future_spec,
            co_new_locals=False,
            co_is_optimized=False,
        )

    def __repr__(self):
        return "<CodeObjectSpecModule '<module>' of module '%s'>" % self.module_name

    def getDetails(self):
        # Only the values needed for the constructor are persisted, the
        # fixed values are implied by this class.
        return {
            "module_name": self.module_name,
            "co_filename": self.filename,
            "code_flags": ",".join(self.future_spec.asFlags()),
        }

    @classmethod
    def fromXML(cls, module_name, co_filename, future_spec):
        """Reconstruct from XML details.

        Args:
            module_name: the name of the module for display purposes.
            co_filename: the filename of the module code.
            future_spec: the future spec of the module.

        Returns:
            Instance of 'CodeObjectSpecModule'.
        """
        return cls(
            module_name=module_name,
            co_filename=co_filename,
            future_spec=future_spec,
        )


class CodeObjectSpecClass(CodeObjectSpec):
    """Code object specification of a class frame.

    Notes:
        Class code objects have fixed values for all argument related details
        and flags, only the name, qualname, variable names, line number,
        filename and future spec vary. In Nuitka they never have free
        variables, captured values are frame variables instead. On Python2
        class code objects are unoptimized, but do get new locals, unlike on
        Python3.
    """

    __slots__ = ()

    def __init__(
        self, class_name, co_qualname, co_varnames, co_filename, co_lineno, future_spec
    ):
        CodeObjectSpec.__init__(
            self,
            co_name=class_name,
            co_qualname=co_qualname,
            co_kind="Class",
            co_varnames=co_varnames,
            co_freevars=(),
            co_argcount=0,
            co_posonlyargcount=0,
            co_kwonlyargcount=0,
            co_has_starlist=False,
            co_has_stardict=False,
            co_filename=co_filename,
            co_lineno=co_lineno,
            future_spec=future_spec,
            co_new_locals=python_version < 0x300,
            co_is_optimized=False,
        )

    def __repr__(self):
        return "<CodeObjectSpecClass '%s' line %d>" % (self.co_name, self.line_number)

    def getDetails(self):
        # Only the values needed for the constructor are persisted, the
        # fixed values are implied by this class.
        return {
            "class_name": self.co_name,
            "co_qualname": self.co_qualname,
            "co_varnames": ",".join(self.co_varnames),
            "co_filename": self.filename,
            "co_lineno": self.line_number,
            "code_flags": ",".join(self.future_spec.asFlags()),
        }

    def updateLocalNames(self, local_names, freevar_names):
        # Class bodies never have free variables in Nuitka, their captured
        # values are frame variables instead.
        assert not freevar_names, freevar_names

        CodeObjectSpec.updateLocalNames(self, local_names, ())

    def setFlagIsOptimizedValue(self, value):
        assert value is False, value

    def getFlagIsOptimizedValue(self):
        return False

    def setFlagNewLocalsValue(self, value):
        assert value == (python_version < 0x300), value

    def getFlagNewLocalsValue(self):
        return python_version < 0x300

    @classmethod
    def fromXML(
        cls, class_name, co_qualname, co_varnames, co_filename, co_lineno, future_spec
    ):
        """Reconstruct from XML details.

        Args:
            class_name: the name of the class for display purposes.
            co_qualname: the qualified name of the class code.
            co_varnames: the variable names of the class code.
            co_filename: the filename of the class code.
            co_lineno: the line number of the class code.
            future_spec: the future spec of the module.

        Returns:
            Instance of 'CodeObjectSpecClass'.
        """
        return cls(
            class_name=class_name,
            co_qualname=co_qualname,
            co_varnames=co_varnames,
            co_filename=co_filename,
            co_lineno=co_lineno,
            future_spec=future_spec,
        )


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
