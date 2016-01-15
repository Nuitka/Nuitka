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
from pybench import Test

class SimpleListManipulation(Test):

    version = 2.0
    operations = 5* (6 + 6 + 6)
    rounds = 130000

    def test(self):

        l = []
        append = l.append

        for i in xrange(self.rounds):

            append(2)
            append(3)
            append(4)
            append(2)
            append(3)
            append(4)

            l[0] = 3
            l[1] = 4
            l[2] = 5
            l[3] = 3
            l[4] = 4
            l[5] = 5

            x = l[0]
            x = l[1]
            x = l[2]
            x = l[3]
            x = l[4]
            x = l[5]

            append(2)
            append(3)
            append(4)
            append(2)
            append(3)
            append(4)

            l[0] = 3
            l[1] = 4
            l[2] = 5
            l[3] = 3
            l[4] = 4
            l[5] = 5

            x = l[0]
            x = l[1]
            x = l[2]
            x = l[3]
            x = l[4]
            x = l[5]

            append(2)
            append(3)
            append(4)
            append(2)
            append(3)
            append(4)

            l[0] = 3
            l[1] = 4
            l[2] = 5
            l[3] = 3
            l[4] = 4
            l[5] = 5

            x = l[0]
            x = l[1]
            x = l[2]
            x = l[3]
            x = l[4]
            x = l[5]

            append(2)
            append(3)
            append(4)
            append(2)
            append(3)
            append(4)

            l[0] = 3
            l[1] = 4
            l[2] = 5
            l[3] = 3
            l[4] = 4
            l[5] = 5

            x = l[0]
            x = l[1]
            x = l[2]
            x = l[3]
            x = l[4]
            x = l[5]

            append(2)
            append(3)
            append(4)
            append(2)
            append(3)
            append(4)

            l[0] = 3
            l[1] = 4
            l[2] = 5
            l[3] = 3
            l[4] = 4
            l[5] = 5

            x = l[0]
            x = l[1]
            x = l[2]
            x = l[3]
            x = l[4]
            x = l[5]

            if len(l) > 10000:
                # cut down the size
                del l[:]

    def calibrate(self):

        l = []
        append = l.append

        for i in xrange(self.rounds):
            pass

class ListSlicing(Test):

    version = 2.0
    operations = 25*(3+1+2+1)
    rounds = 800

    def test(self):

        n = range(100)
        r = range(25)

        for i in xrange(self.rounds):

            l = n[:]

            for j in r:

                m = l[50:]
                m = l[:25]
                m = l[50:55]
                l[:3] = n
                m = l[:-1]
                m = l[1:]
                l[-1:] = n

    def calibrate(self):

        n = range(100)
        r = range(25)

        for i in xrange(self.rounds):
            for j in r:
                pass

class SmallLists(Test):

    version = 2.0
    operations = 5*(1+ 6 + 6 + 3 + 1)
    rounds = 80000

    def test(self):

        for i in xrange(self.rounds):

            l = []

            append = l.append
            append(2)
            append(3)
            append(4)
            append(2)
            append(3)
            append(4)

            l[0] = 3
            l[1] = 4
            l[2] = 5
            l[3] = 3
            l[4] = 4
            l[5] = 5

            l[:3] = [1,2,3]
            m = l[:-1]
            m = l[1:]

            l[-1:] = [4,5,6]

            l = []

            append = l.append
            append(2)
            append(3)
            append(4)
            append(2)
            append(3)
            append(4)

            l[0] = 3
            l[1] = 4
            l[2] = 5
            l[3] = 3
            l[4] = 4
            l[5] = 5

            l[:3] = [1,2,3]
            m = l[:-1]
            m = l[1:]

            l[-1:] = [4,5,6]

            l = []

            append = l.append
            append(2)
            append(3)
            append(4)
            append(2)
            append(3)
            append(4)

            l[0] = 3
            l[1] = 4
            l[2] = 5
            l[3] = 3
            l[4] = 4
            l[5] = 5

            l[:3] = [1,2,3]
            m = l[:-1]
            m = l[1:]

            l[-1:] = [4,5,6]

            l = []

            append = l.append
            append(2)
            append(3)
            append(4)
            append(2)
            append(3)
            append(4)

            l[0] = 3
            l[1] = 4
            l[2] = 5
            l[3] = 3
            l[4] = 4
            l[5] = 5

            l[:3] = [1,2,3]
            m = l[:-1]
            m = l[1:]

            l[-1:] = [4,5,6]

            l = []

            append = l.append
            append(2)
            append(3)
            append(4)
            append(2)
            append(3)
            append(4)

            l[0] = 3
            l[1] = 4
            l[2] = 5
            l[3] = 3
            l[4] = 4
            l[5] = 5

            l[:3] = [1,2,3]
            m = l[:-1]
            m = l[1:]

            l[-1:] = [4,5,6]

    def calibrate(self):

        for i in xrange(self.rounds):
            pass

class SimpleListComprehensions(Test):

    version = 2.0
    operations = 6
    rounds = 20000

    def test(self):

        n = range(10) * 10

        for i in xrange(self.rounds):
            l = [x for x in n]
            l = [x for x in n if x]
            l = [x for x in n if not x]

            l = [x for x in n]
            l = [x for x in n if x]
            l = [x for x in n if not x]

    def calibrate(self):

        n = range(10) * 10

        for i in xrange(self.rounds):
            pass

class NestedListComprehensions(Test):

    version = 2.0
    operations = 6
    rounds = 20000

    def test(self):

        m = range(10)
        n = range(10)

        for i in xrange(self.rounds):
            l = [x for x in n for y in m]
            l = [y for x in n for y in m]

            l = [x for x in n for y in m if y]
            l = [y for x in n for y in m if x]

            l = [x for x in n for y in m if not y]
            l = [y for x in n for y in m if not x]

    def calibrate(self):

        m = range(10)
        n = range(10)

        for i in xrange(self.rounds):
            pass
