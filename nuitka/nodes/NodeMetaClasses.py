#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Node meta classes."""

from abc import ABCMeta

from nuitka.__past__ import intern
from nuitka.Errors import NuitkaAssumptionError, NuitkaNodeDesignError
from nuitka.PythonVersions import python_version
from nuitka.utils.SlotMetaClasses import checkSlots


def _checkBases(name, bases):
    assert len(bases) == len(set(bases)), (name, bases)

    last_mixin = None
    for base in bases:
        base_name = base.__name__
        is_mixin = base_name.endswith("Mixin")

        if is_mixin and last_mixin is False:
            raise NuitkaNodeDesignError(
                name, "Mixins must come first in base classes.", bases
            )

        last_mixin = is_mixin

        if not isinstance(base, type):
            raise NuitkaNodeDesignError(
                name, "All bases must inherit from object.", base
            )

        if base is not object and "__slots__" not in base.__dict__:
            raise NuitkaNodeDesignError(name, "All bases must set __slots__.", base)


def _getUnboundFunction(method):
    # Python 2 wraps methods as unbound instancemethods whose identity differs per class.
    return getattr(method, "__func__", method)


def _collectCloningSpec(cls):
    named_children = ()
    node_attributes = []

    for base in cls.__mro__:
        if not named_children and "named_children" in base.__dict__:
            named_children = base.__dict__["named_children"]

        if "node_attributes" in base.__dict__:
            node_attributes.extend(base.__dict__["node_attributes"])

    child_param_names = set(
        "object_arg" if nc.split("|", 1)[0] == "object" else nc.split("|", 1)[0]
        for nc in named_children
    )

    return named_children, child_param_names, tuple(node_attributes)


def _checkInitParameters(name, all_args, has_varkw, expected_names, label):
    if has_varkw:
        return

    missing = sorted(expected_names - all_args)
    if missing:
        raise NuitkaNodeDesignError(
            name,
            "Node '__init__' does not accept '%s' parameters." % label,
            tuple(missing),
        )


def _checkCloningInterface(cls, name):
    from .NodeBases import NodeBase

    if _getUnboundFunction(cls.makeClone) is not _getUnboundFunction(
        NodeBase.makeClone
    ):
        return

    init_func = _getUnboundFunction(cls.__init__)
    if getattr(init_func, "is_version_disabled", False):
        return

    code = getattr(init_func, "__code__", None)
    if code is None:
        return

    arg_names = code.co_varnames[1 : code.co_argcount]
    defaults = getattr(init_func, "__defaults__", None) or ()
    required_args = set(arg_names[: len(arg_names) - len(defaults)])
    all_args = set(arg_names)
    has_varkw = bool(code.co_flags & 0x08)

    named_children, child_param_names, node_attributes = _collectCloningSpec(cls)

    if named_children:
        if _getUnboundFunction(cls.getCloneArgs) is _getUnboundFunction(
            NodeBase.getCloneArgs
        ):
            raise NuitkaNodeDesignError(
                name,
                "Node defines 'named_children' without overriding 'getCloneArgs'.",
                named_children,
            )

        _checkInitParameters(
            name, all_args, has_varkw, child_param_names, "named_children"
        )

    uses_default_get_details = _getUnboundFunction(
        cls.getDetails
    ) is _getUnboundFunction(NodeBase.getDetails)

    if node_attributes:
        if uses_default_get_details:
            raise NuitkaNodeDesignError(
                name,
                "Node defines 'node_attributes' without overriding 'getDetails'.",
                node_attributes,
            )

        _checkInitParameters(
            name, all_args, has_varkw, set(node_attributes), "node_attributes"
        )

    non_child_required = sorted(
        required_args - child_param_names - set(("source_ref",))
    )
    if non_child_required and uses_default_get_details:
        raise NuitkaNodeDesignError(
            name,
            "Node '__init__' requires non-child parameters without overriding 'getDetails'.",
            tuple(non_child_required),
        )


def returnFalseSharedFunction():
    return False


returnFalseShared = staticmethod(returnFalseSharedFunction)


class NodeCheckMetaClass(ABCMeta):
    kinds = {}

    def __new__(mcs, name, bases, dictionary):  # pylint: disable=I0021,arguments-differ
        _checkBases(name, bases)

        if "__slots__" not in dictionary:
            dictionary["__slots__"] = ()
        elif type(dictionary["__slots__"]) is not tuple:
            raise NuitkaNodeDesignError(
                name, "Class __slots__ must be a tuple.", dictionary["__slots__"]
            )

        if "named_children" in dictionary:
            assert type(dictionary["named_children"]) is tuple

            for base in bases:
                for ancestor in base.__mro__:
                    if "named_children" in ancestor.__dict__:
                        raise NuitkaNodeDesignError(
                            name,
                            "Redeclared 'named_children' from %s." % ancestor.__name__,
                            dictionary["named_children"],
                        )

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

        checkSlots(name=name, bases=bases, dictionary=dictionary)

        python_version_spec = dictionary.get("python_version_spec")

        if python_version_spec:
            condition = " and ".join(
                "%s %s" % (hex(python_version), spec.strip())
                for spec in python_version_spec.split(",")
                if spec.strip()
            )
            assert condition, python_version_spec

            # pylint: disable=eval-used
            if not eval(condition):

                def __init__(self, *args, **kwargs):
                    raise NuitkaAssumptionError(name, "assumption violated", condition)

                __init__.is_version_disabled = True
                dictionary["__init__"] = __init__

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

            checker_method_name = "is" + kind_to_name_part

            from .NodeBases import NodeBase

            if not hasattr(NodeBase, checker_method_name):
                setattr(NodeBase, checker_method_name, returnFalseShared)

        ABCMeta.__init__(cls, name, bases, dictionary)

        if not name.endswith(("Base", "Mixin")):
            if getattr(cls, checker_method_name) is returnFalseSharedFunction:

                def checkKind(self):
                    return self.kind == kind

                setattr(cls, checker_method_name, checkKind)

            _checkCloningInterface(cls, name)


# For Python2/3 compatible source, we create a base class that has the metaclass
# used and doesn't require making a syntax choice.
NodeMetaClassBase = NodeCheckMetaClass(
    "NodeMetaClassBase", (object,), {"__slots__": ()}
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
