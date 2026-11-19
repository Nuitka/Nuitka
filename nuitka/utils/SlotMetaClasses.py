#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Helper for portable metaclasses that do checks."""

from abc import ABCMeta

from nuitka.Errors import NuitkaNodeDesignError


def checkSlots(name, bases, dictionary):
    slots = dictionary["__slots__"]

    if type(slots) is not tuple:
        raise NuitkaNodeDesignError(name, "Class __slots__ must be a tuple.", slots)

    if slots:
        if len(slots) != len(set(slots)):
            raise NuitkaNodeDesignError(name, "Duplicate __slots__ entries.", slots)

        for base in bases:
            for ancestor in base.__mro__:
                if ancestor is object:
                    continue

                duplicate_slots = tuple(
                    slot
                    for slot in slots
                    if slot in ancestor.__dict__.get("__slots__", ())
                )

                if duplicate_slots:
                    raise NuitkaNodeDesignError(
                        name,
                        "Redeclared inherited __slots__ from %s." % ancestor.__name__,
                        duplicate_slots,
                    )


def getMetaClassBase(meta_class_prefix, require_slots):
    """For Python2/3 compatible source, we create a base class that has the metaclass
    used and doesn't require making a syntax choice.

    Also this allows to enforce the proper usage of "__slots__" for all classes using
    it optionally.
    """

    class MetaClass(ABCMeta):
        def __new__(
            mcs, name, bases, dictionary
        ):  # pylint: disable=I0021,arguments-differ
            if require_slots:
                for base in bases:
                    if not isinstance(base, type):
                        raise NuitkaNodeDesignError(
                            name, "All bases must inherit from object.", base
                        )

                    if base is not object and "__slots__" not in base.__dict__:
                        raise NuitkaNodeDesignError(
                            name, "All bases must set __slots__.", base
                        )

                if "__slots__" not in dictionary:
                    raise NuitkaNodeDesignError(name, "Class must set __slots__.", name)

                checkSlots(name=name, bases=bases, dictionary=dictionary)

            return ABCMeta.__new__(mcs, name, bases, dictionary)

    MetaClassBase = MetaClass(
        "%sMetaClassBase" % meta_class_prefix,
        (object,),
        {"__slots__": ()} if require_slots else {},
    )

    return MetaClassBase


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
