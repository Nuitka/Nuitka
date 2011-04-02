#
#     Kay Hayen, mailto:kayhayen@gmx.de
#
#     Python test originally created or extracted from other peoples work. The
#     parts from me are in the public domain. It is at least Free Software
#     where it's copied from other people. In these cases, it will normally be
#     indicated.
#
#     If you submit Kay Hayen patches to this software in either form, you
#     automatically grant him a copyright assignment to the code, or in the
#     alternative a BSD license to the code, should your jurisdiction prevent
#     this. Obviously it won't affect code that comes to him indirectly or
#     code you don't submit to him.
#
#     This is to reserve my ability to re-license the code at any time, e.g.
#     the PSF. With this version of Nuitka, using it for Closed Source will
#     not be allowed.
#
#     Please leave the whole of this copyright notice intact.
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
