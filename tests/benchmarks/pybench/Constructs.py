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

class IfThenElse(Test):

    version = 2.0
    operations = 30*3 # hard to say...
    rounds = 150000

    def test(self):

        a,b,c = 1,2,3
        for i in xrange(self.rounds):

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

            if a == 1:
                if b == 2:
                    if c != 3:
                        c = 3
                        b = 3
                    else:
                        c = 2
                elif b == 3:
                    b = 2
                    a = 2
            elif a == 2:
                a = 3
            else:
                a = 1

    def calibrate(self):

        a,b,c = 1,2,3
        for i in xrange(self.rounds):
            pass

class NestedForLoops(Test):

    version = 2.0
    operations = 1000*10*5
    rounds = 300

    def test(self):

        l1 = range(1000)
        l2 = range(10)
        l3 = range(5)
        for i in xrange(self.rounds):
            for i in l1:
                for j in l2:
                    for k in l3:
                        pass

    def calibrate(self):

        l1 = range(1000)
        l2 = range(10)
        l3 = range(5)
        for i in xrange(self.rounds):
            pass

class ForLoops(Test):

    version = 2.0
    operations = 5 * 5
    rounds = 10000

    def test(self):

        l1 = range(100)
        for i in xrange(self.rounds):
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass

            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass

            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass

            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass

            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass
            for i in l1:
                pass

    def calibrate(self):

        l1 = range(1000)
        for i in xrange(self.rounds):
            pass
