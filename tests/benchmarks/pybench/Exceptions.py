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

class TryRaiseExcept(Test):

    version = 2.0
    operations = 2 + 3 + 3
    rounds = 80000

    def test(self):

        error = ValueError

        for i in xrange(self.rounds):
            try:
                raise error
            except:
                pass
            try:
                raise error
            except:
                pass
            try:
                raise error,"something"
            except:
                pass
            try:
                raise error,"something"
            except:
                pass
            try:
                raise error,"something"
            except:
                pass
            try:
                raise error("something")
            except:
                pass
            try:
                raise error("something")
            except:
                pass
            try:
                raise error("something")
            except:
                pass

    def calibrate(self):

        error = ValueError

        for i in xrange(self.rounds):
            pass


class TryExcept(Test):

    version = 2.0
    operations = 15 * 10
    rounds = 150000

    def test(self):

        for i in xrange(self.rounds):
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass

            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass


            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass


            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass


            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass

            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass

            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass


            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass


            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass


            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass

            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass

            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass


            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass


            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass


            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass
            try:
                pass
            except:
                pass

    def calibrate(self):

        for i in xrange(self.rounds):
            pass

### Test to make Fredrik happy...

if __name__ == '__main__':
    import timeit
    timeit.TestClass = TryRaiseExcept
    timeit.main(['-s', 'test = TestClass(); test.rounds = 1000',
                 'test.test()'])
