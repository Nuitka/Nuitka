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

class SimpleIntegerArithmetic(Test):

    version = 2.0
    operations = 5 * (3 + 5 + 5 + 3 + 3 + 3)
    rounds = 120000

    def test(self):

        for i in xrange(self.rounds):

            a = 2
            b = 3
            c = 3

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

    def calibrate(self):

        for i in xrange(self.rounds):
            pass

class SimpleFloatArithmetic(Test):

    version = 2.0
    operations = 5 * (3 + 5 + 5 + 3 + 3 + 3)
    rounds = 120000

    def test(self):

        for i in xrange(self.rounds):

            a = 2.1
            b = 3.3332
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2.1
            b = 3.3332
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2.1
            b = 3.3332
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2.1
            b = 3.3332
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2.1
            b = 3.3332
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

    def calibrate(self):

        for i in xrange(self.rounds):
            pass

class SimpleIntFloatArithmetic(Test):

    version = 2.0
    operations = 5 * (3 + 5 + 5 + 3 + 3 + 3)
    rounds = 120000

    def test(self):

        for i in xrange(self.rounds):

            a = 2
            b = 3
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2
            b = 3
            c = 3.14159

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

    def calibrate(self):

        for i in xrange(self.rounds):
            pass


class SimpleLongArithmetic(Test):

    version = 2.0
    operations = 5 * (3 + 5 + 5 + 3 + 3 + 3)
    rounds = 60000

    def test(self):

        for i in xrange(self.rounds):

            a = 2220001L
            b = 100001L
            c = 30005L

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2220001L
            b = 100001L
            c = 30005L

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2220001L
            b = 100001L
            c = 30005L

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2220001L
            b = 100001L
            c = 30005L

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2220001L
            b = 100001L
            c = 30005L

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

    def calibrate(self):

        for i in xrange(self.rounds):
            pass

class SimpleComplexArithmetic(Test):

    version = 2.0
    operations = 5 * (3 + 5 + 5 + 3 + 3 + 3)
    rounds = 80000

    def test(self):

        for i in xrange(self.rounds):

            a = 2 + 3j
            b = 2.5 + 4.5j
            c = 1.2 + 6.2j

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2 + 3j
            b = 2.5 + 4.5j
            c = 1.2 + 6.2j

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2 + 3j
            b = 2.5 + 4.5j
            c = 1.2 + 6.2j

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2 + 3j
            b = 2.5 + 4.5j
            c = 1.2 + 6.2j

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

            a = 2 + 3j
            b = 2.5 + 4.5j
            c = 1.2 + 6.2j

            c = a + b
            c = b + c
            c = c + a
            c = a + b
            c = b + c

            c = c - a
            c = a - b
            c = b - c
            c = c - a
            c = b - c

            c = a / b
            c = b / a
            c = c / b

            c = a * b
            c = b * a
            c = c * b

            c = a / b
            c = b / a
            c = c / b

    def calibrate(self):

        for i in xrange(self.rounds):
            pass
