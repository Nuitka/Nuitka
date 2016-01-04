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

class SpecialClassAttribute(Test):

    version = 2.0
    operations = 5*(12 + 12)
    rounds = 100000

    def test(self):

        class c:
            pass

        for i in xrange(self.rounds):

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            c.__a = 2
            c.__b = 3
            c.__c = 4

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

            x = c.__a
            x = c.__b
            x = c.__c

    def calibrate(self):

        class c:
            pass

        for i in xrange(self.rounds):
            pass

class NormalClassAttribute(Test):

    version = 2.0
    operations = 5*(12 + 12)
    rounds = 100000

    def test(self):

        class c:
            pass

        for i in xrange(self.rounds):

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4


            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4


            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4


            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4


            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4

            c.a = 2
            c.b = 3
            c.c = 4


            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

            x = c.a
            x = c.b
            x = c.c

    def calibrate(self):

        class c:
            pass

        for i in xrange(self.rounds):
            pass

class SpecialInstanceAttribute(Test):

    version = 2.0
    operations = 5*(12 + 12)
    rounds = 100000

    def test(self):

        class c:
            pass
        o = c()

        for i in xrange(self.rounds):

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4


            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4


            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4


            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4


            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4

            o.__a__ = 2
            o.__b__ = 3
            o.__c__ = 4


            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

            x = o.__a__
            x = o.__b__
            x = o.__c__

    def calibrate(self):

        class c:
            pass
        o = c()

        for i in xrange(self.rounds):
            pass

class NormalInstanceAttribute(Test):

    version = 2.0
    operations = 5*(12 + 12)
    rounds = 100000

    def test(self):

        class c:
            pass
        o = c()

        for i in xrange(self.rounds):

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4


            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4


            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4


            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4


            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4

            o.a = 2
            o.b = 3
            o.c = 4


            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

            x = o.a
            x = o.b
            x = o.c

    def calibrate(self):

        class c:
            pass
        o = c()

        for i in xrange(self.rounds):
            pass

class BuiltinMethodLookup(Test):

    version = 2.0
    operations = 5*(3*5 + 3*5)
    rounds = 70000

    def test(self):

        l = []
        d = {}

        for i in xrange(self.rounds):

            l.append
            l.append
            l.append
            l.append
            l.append

            l.insert
            l.insert
            l.insert
            l.insert
            l.insert

            l.sort
            l.sort
            l.sort
            l.sort
            l.sort

            d.has_key
            d.has_key
            d.has_key
            d.has_key
            d.has_key

            d.items
            d.items
            d.items
            d.items
            d.items

            d.get
            d.get
            d.get
            d.get
            d.get

            l.append
            l.append
            l.append
            l.append
            l.append

            l.insert
            l.insert
            l.insert
            l.insert
            l.insert

            l.sort
            l.sort
            l.sort
            l.sort
            l.sort

            d.has_key
            d.has_key
            d.has_key
            d.has_key
            d.has_key

            d.items
            d.items
            d.items
            d.items
            d.items

            d.get
            d.get
            d.get
            d.get
            d.get

            l.append
            l.append
            l.append
            l.append
            l.append

            l.insert
            l.insert
            l.insert
            l.insert
            l.insert

            l.sort
            l.sort
            l.sort
            l.sort
            l.sort

            d.has_key
            d.has_key
            d.has_key
            d.has_key
            d.has_key

            d.items
            d.items
            d.items
            d.items
            d.items

            d.get
            d.get
            d.get
            d.get
            d.get

            l.append
            l.append
            l.append
            l.append
            l.append

            l.insert
            l.insert
            l.insert
            l.insert
            l.insert

            l.sort
            l.sort
            l.sort
            l.sort
            l.sort

            d.has_key
            d.has_key
            d.has_key
            d.has_key
            d.has_key

            d.items
            d.items
            d.items
            d.items
            d.items

            d.get
            d.get
            d.get
            d.get
            d.get

            l.append
            l.append
            l.append
            l.append
            l.append

            l.insert
            l.insert
            l.insert
            l.insert
            l.insert

            l.sort
            l.sort
            l.sort
            l.sort
            l.sort

            d.has_key
            d.has_key
            d.has_key
            d.has_key
            d.has_key

            d.items
            d.items
            d.items
            d.items
            d.items

            d.get
            d.get
            d.get
            d.get
            d.get

    def calibrate(self):

        l = []
        d = {}

        for i in xrange(self.rounds):
            pass
