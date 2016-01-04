#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
# This taken from CPython's pystone test, and is an extract of it I made to analyse the
# differences between CPython and Nuitka performance. It was under PSF 2 license. It's not
# very useful anymore, but it is under that license still.

from time import clock

LOOPS = 5000000
__version__ = "1.1"

Char1Glob = 'A'
IntGlob = 8

Ident1 = "lalala"

count = 0

def Proc2(IntParIO):
    global count

    IntLoc = IntParIO + 10
    while 1:
        count += 1

        if Char1Glob == 'A':
            IntLoc = IntLoc - 1
            IntParIO = IntLoc - IntGlob
            EnumLoc = Ident1
        if EnumLoc == Ident1:
            break
    return IntParIO

def benchmark(loops):
    for i in xrange(loops):
        Proc2(17)

if __name__ == "__main__":
    benchmark(LOOPS)
    assert count == LOOPS
