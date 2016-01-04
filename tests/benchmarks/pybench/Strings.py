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
from string import join

class ConcatStrings(Test):

    version = 2.0
    operations = 10 * 5
    rounds = 100000

    def test(self):

        # Make sure the strings are *not* interned
        s = join(map(str,range(100)))
        t = join(map(str,range(1,101)))

        for i in xrange(self.rounds):
            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

            t + s
            t + s
            t + s
            t + s
            t + s

    def calibrate(self):

        s = join(map(str,range(100)))
        t = join(map(str,range(1,101)))

        for i in xrange(self.rounds):
            pass


class CompareStrings(Test):

    version = 2.0
    operations = 10 * 5
    rounds = 200000

    def test(self):

        # Make sure the strings are *not* interned
        s = join(map(str,range(10)))
        t = join(map(str,range(10))) + "abc"

        for i in xrange(self.rounds):
            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

            t < s
            t > s
            t == s
            t > s
            t < s

    def calibrate(self):

        s = join(map(str,range(10)))
        t = join(map(str,range(10))) + "abc"

        for i in xrange(self.rounds):
            pass


class CompareInternedStrings(Test):

    version = 2.0
    operations = 10 * 5
    rounds = 300000

    def test(self):

        # Make sure the strings *are* interned
        s = intern(join(map(str,range(10))))
        t = s

        for i in xrange(self.rounds):
            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

            t == s
            t == s
            t >= s
            t > s
            t < s

    def calibrate(self):

        s = intern(join(map(str,range(10))))
        t = s

        for i in xrange(self.rounds):
            pass


class CreateStringsWithConcat(Test):

    version = 2.0
    operations = 10 * 5
    rounds = 200000

    def test(self):

        for i in xrange(self.rounds):
            s = 'om'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

            s = s + 'xax'
            s = s + 'xbx'
            s = s + 'xcx'
            s = s + 'xdx'
            s = s + 'xex'

    def calibrate(self):

        for i in xrange(self.rounds):
            pass


class StringSlicing(Test):

    version = 2.0
    operations = 5 * 7
    rounds = 160000

    def test(self):

        s = join(map(str,range(100)))

        for i in xrange(self.rounds):

            s[50:]
            s[:25]
            s[50:55]
            s[-1:]
            s[:1]
            s[2:]
            s[11:-11]

            s[50:]
            s[:25]
            s[50:55]
            s[-1:]
            s[:1]
            s[2:]
            s[11:-11]

            s[50:]
            s[:25]
            s[50:55]
            s[-1:]
            s[:1]
            s[2:]
            s[11:-11]

            s[50:]
            s[:25]
            s[50:55]
            s[-1:]
            s[:1]
            s[2:]
            s[11:-11]

            s[50:]
            s[:25]
            s[50:55]
            s[-1:]
            s[:1]
            s[2:]
            s[11:-11]

    def calibrate(self):

        s = join(map(str,range(100)))

        for i in xrange(self.rounds):
            pass

### String methods

if hasattr('', 'lower'):

    class StringMappings(Test):

        version = 2.0
        operations = 3 * (5 + 4 + 2 + 1)
        rounds = 70000

        def test(self):

            s = join(map(chr,range(20)),'')
            t = join(map(chr,range(50)),'')
            u = join(map(chr,range(100)),'')
            v = join(map(chr,range(256)),'')

            for i in xrange(self.rounds):

                s.lower()
                s.lower()
                s.lower()
                s.lower()
                s.lower()

                s.upper()
                s.upper()
                s.upper()
                s.upper()
                s.upper()

                s.title()
                s.title()
                s.title()
                s.title()
                s.title()

                t.lower()
                t.lower()
                t.lower()
                t.lower()

                t.upper()
                t.upper()
                t.upper()
                t.upper()

                t.title()
                t.title()
                t.title()
                t.title()

                u.lower()
                u.lower()

                u.upper()
                u.upper()

                u.title()
                u.title()

                v.lower()

                v.upper()

                v.title()

        def calibrate(self):

            s = join(map(chr,range(20)),'')
            t = join(map(chr,range(50)),'')
            u = join(map(chr,range(100)),'')
            v = join(map(chr,range(256)),'')

            for i in xrange(self.rounds):
                pass

    class StringPredicates(Test):

        version = 2.0
        operations = 10 * 7
        rounds = 100000

        def test(self):

            data = ('abc', '123', '   ', '\xe4\xf6\xfc', '\xdf'*10)
            len_data = len(data)

            for i in xrange(self.rounds):
                s = data[i % len_data]

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

                s.isalnum()
                s.isalpha()
                s.isdigit()
                s.islower()
                s.isspace()
                s.istitle()
                s.isupper()

        def calibrate(self):

            data = ('abc', '123', '   ', '\u1234\u2345\u3456', '\uFFFF'*10)
            data = ('abc', '123', '   ', '\xe4\xf6\xfc', '\xdf'*10)
            len_data = len(data)

            for i in xrange(self.rounds):
                s = data[i % len_data]
