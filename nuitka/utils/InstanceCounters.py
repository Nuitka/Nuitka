#     Copyright 2023, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Instance counter primitives

We don't use a meta class as it's unnecessary complex, and portable meta classes
have their difficulties, and want to count classes, who already have a meta
class.

This is going to expanded with time.

"""
from nuitka.Options import isShowMemory
from nuitka.Tracing import printIndented, printLine

counted_inits = {}
counted_dels = {}


def isCountingInstances():
    return isShowMemory()


def counted_init(init):
    if isShowMemory():

        def wrapped_init(self, *args, **kw):
            name = self.__class__.__name__
            assert type(name) is str

            if name not in counted_inits:
                counted_inits[name] = 0

            counted_inits[name] += 1

            init(self, *args, **kw)

        return wrapped_init
    else:
        return init


def _wrapped_del(self):
    # This cannot be necessary, because in program finalization, the
    # global variables were assign to None.
    if counted_dels is None:
        return

    name = self.__class__.__name__
    assert type(name) is str

    if name not in counted_dels:
        counted_dels[name] = 0

    counted_dels[name] += 1


def counted_del():
    assert isShowMemory()

    return _wrapped_del


def printStats():
    printLine("Init/del/alive calls:")

    for name, count in sorted(counted_inits.items()):
        dels = counted_dels.get(name, 0)
        printIndented(1, name, count, dels, count - dels)
