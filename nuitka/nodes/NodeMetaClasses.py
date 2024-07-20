#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Node meta classes.

This provides meta classes for nodes, currently only one. These do all kinds
of checks, and add methods automatically.

"""

from abc import ABCMeta

from nuitka.__past__ import intern
from nuitka.Errors import NuitkaAssumptionError, NuitkaNodeDesignError
from nuitka.PythonVersions import python_version


def _checkBases(name, bases):
    # Avoid duplicate base classes.
    assert len(bases) == len(set(bases)), (name, bases)

    # Insist on mixins being in proper place for inheritance.
    last_mixin = None
    for base in bases:
        base_name = base.__name__
        is_mixin = base_name.endswith("Mixin")

        if is_mixin and last_mixin is False:
            raise NuitkaNodeDesignError(
                name, "Mixins must come first in base classes.", bases
            )

        last_mixin = is_mixin

        if base is not object and "__slots__" not in base.__dict__:
            raise NuitkaNodeDesignError(name, "All bases must set __slots__.", base)


@staticmethod
def returnTrueShared():
    return True


@staticmethod
def returnFalseShared():
    return False


class NodeCheckMetaClass(ABCMeta):
    kinds = {}

    def __new__(mcs, name, bases, dictionary):  # pylint: disable=I0021,arguments-differ
        _checkBases(name, bases)

        if "__slots__" not in dictionary:
            dictionary["__slots__"] = ()

        if "named_children" in dictionary:
            assert type(dictionary["named_children"]) is tuple

            dictionary["__slots__"] += tuple(
                intern("subnode_" + named_child.split("|", 1)[0])
                for named_child in dictionary["named_children"]
            )

        if "nice_children" in dictionary:
            assert type(dictionary["nice_children"]) is tuple
            assert len(dictionary["nice_children"]) == len(dictionary["named_children"])

            dictionary["nice_children_dict"] = dict(
                (intern(named_child.split("|", 1)[0]), nice_name)
                for (named_child, nice_name) in zip(
                    dictionary["named_children"], dictionary["nice_children"]
                )
            )

        if "node_attributes" in dictionary:
            dictionary["__slots__"] += dictionary["node_attributes"]

        assert len(dictionary["__slots__"]) == len(
            set(dictionary["__slots__"])
        ), dictionary["__slots__"]

        if "python_version_spec" in dictionary:
            condition = "%s %s" % (
                hex(python_version),
                dictionary["python_version_spec"],
            )

            # We trust our node class files, pylint: disable=eval-used
            if not eval(condition):

                def __init__(self, *args, **kwargs):
                    raise NuitkaAssumptionError(name, "assumption violated", condition)

                dictionary["__init__"] = __init__

        # Not a method:
        if "checker" in dictionary:
            dictionary["checker"] = staticmethod(dictionary["checker"])

        return ABCMeta.__new__(mcs, name, bases, dictionary)

    def __init__(cls, name, bases, dictionary):
        if not name.endswith(("Base", "Mixin")):
            if "kind" not in dictionary:
                raise NuitkaNodeDesignError(name, "Must provide class variable 'kind'")

            kind = dictionary["kind"]

            assert type(kind) is str, name

            if kind in NodeCheckMetaClass.kinds and "replaces" not in dictionary:
                raise NuitkaNodeDesignError(
                    name, "Duplicate nodes for kind '%s'" % kind
                )

            NodeCheckMetaClass.kinds[kind] = cls
            NodeCheckMetaClass.kinds[name] = cls

            kind_to_name_part = "".join([x.capitalize() for x in kind.split("_")])
            assert name.endswith(kind_to_name_part), (name, kind_to_name_part)

            # Automatically add checker methods for everything to the common
            # base class
            checker_method_name = "is" + kind_to_name_part

            # Add automatic checker "False" to the node base class.
            from .NodeBases import NodeBase

            if not hasattr(NodeBase, checker_method_name):
                setattr(NodeBase, checker_method_name, returnFalseShared)

        ABCMeta.__init__(cls, name, bases, dictionary)

        if not name.endswith(("Base", "Mixin")):
            if kind.startswith("EXPRESSION_BUILTIN_"):
                cls.isExpressionBuiltin = returnTrueShared

            # Add automatic checker "True" to the node class.
            if getattr(cls, checker_method_name) is returnFalseShared.__func__:

                def checkKind(self):
                    return self.kind == kind

                setattr(cls, checker_method_name, checkKind)


# For every node type, there is a test, and then some more members,

# For Python2/3 compatible source, we create a base class that has the metaclass
# used and doesn't require making a syntax choice.
NodeMetaClassBase = NodeCheckMetaClass(
    "NodeMetaClassBase", (object,), {"__slots__": ()}
)

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
