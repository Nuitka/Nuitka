#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" This module is only an abstraction of namedtuple.

It works around bugs present in some version of Python, and provides extra
methods like "asDict".
"""

from collections import namedtuple


def makeNamedtupleClass(name, element_names):
    # TODO: Have a namedtuple factory that does these things.

    namedtuple_class = namedtuple(name, element_names)

    class DynamicNamedtuple(namedtuple_class):
        __qualname__ = name

        # Avoids bugs on early Python3.4 and Python3.5 versions.
        __slots__ = ()

        def asDict(self):
            return self._asdict()

        def replace(self, **kwargs):
            new_data = self.asDict()
            new_data.update(**kwargs)

            return self.__class__(**new_data)

    DynamicNamedtuple.__name__ = name

    return DynamicNamedtuple


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
