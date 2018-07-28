#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Node meta classes.

This provides meta classes for nodes, currently only one. These do all kinds
of checks, and add methods automatically.

"""

from abc import ABCMeta

from nuitka.__past__ import intern  # pylint: disable=I0021,redefined-builtin


def _checkBases(name, bases):
    # Avoid duplicate base classes.
    assert len(bases) == len(set(bases)), (name, bases)

    # Insist on mixins being in proper place for inheritence.
    last_mixin = None
    for base in bases:
        base_name = base.__name__
        is_mixin = base_name.endswith("Mixin")

        if is_mixin and last_mixin is False:
            assert False, (name, bases)

        last_mixin = is_mixin


class NodeCheckMetaClass(ABCMeta):
    kinds = {}

    # This is in conflict with either PyDev or Pylint 1.9.2 used fo Python2, it
    # should be "mcs" for one and "cls" for the other.
    # pylint: disable=I0021,bad-mcs-classmethod-argument

    def __new__(cls, name, bases, dictionary): # pylint: disable=I0021,arguments-differ
        _checkBases(name, bases)

        if "__slots__" not in dictionary:
            dictionary["__slots__"] = ()

        if "named_child" in dictionary:
            dictionary["__slots__"] += (intern("subnode_" + dictionary["named_child"]),)

        # Not a method:
        if "checker" in dictionary:
            dictionary["checker"] = staticmethod(dictionary["checker"])

        return ABCMeta.__new__(cls, name, bases, dictionary)

    def __init__(cls, name, bases, dictionary):  # @NoSelf

        if not name.endswith("Base"):
            assert ("kind" in dictionary), name
            kind = dictionary["kind"]

            assert type(kind) is str, name
            assert kind not in NodeCheckMetaClass.kinds, name

            NodeCheckMetaClass.kinds[kind] = cls
            NodeCheckMetaClass.kinds[name] = cls

            def convert(value):
                if value in ("AND", "OR", "NOT"):
                    return value
                else:
                    return value.title()

            kind_to_name_part = "".join(
                [convert(x) for x in kind.split('_')]
            )
            assert name.endswith(kind_to_name_part), \
              (name, kind_to_name_part)

            # Automatically add checker methods for everything to the common
            # base class
            checker_method = "is" + kind_to_name_part

            # TODO: How about making these two functions, one to statically
            # return True and False, and put one in the base class, and one
            # in the new class, would be slightly faster.
            def checkKind(self):
                return self.kind == kind

            # Add automatic checker methods to the node base class.
            from .NodeBases import NodeBase

            if not hasattr(NodeBase, checker_method):
                setattr(NodeBase, checker_method, checkKind)

        ABCMeta.__init__(cls, name, bases, dictionary)

# For every node type, there is a test, and then some more members,

# For Python2/3 compatible source, we create a base class that has the metaclass
# used and doesn't require making a syntax choice.
NodeMetaClassBase = NodeCheckMetaClass(
    "NodeMetaClassBase",
    (object,),
    {
        "__slots__" : ()
    }
)
