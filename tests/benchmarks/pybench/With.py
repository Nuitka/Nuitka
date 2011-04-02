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
from __future__ import with_statement
from pybench import Test

class WithFinally(Test):

    version = 2.0
    operations = 20
    rounds = 80000

    class ContextManager(object):
        def __enter__(self):
            pass
        def __exit__(self, exc, val, tb):
            pass

    def test(self):

        cm = self.ContextManager()

        for i in xrange(self.rounds):
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass
            with cm: pass

    def calibrate(self):

        cm = self.ContextManager()

        for i in xrange(self.rounds):
            pass


class TryFinally(Test):

    version = 2.0
    operations = 20
    rounds = 80000

    class ContextManager(object):
        def __enter__(self):
            pass
        def __exit__(self):
            # "Context manager" objects used just for their cleanup
            # actions in finally blocks usually don't have parameters.
            pass

    def test(self):

        cm = self.ContextManager()

        for i in xrange(self.rounds):
            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

            cm.__enter__()
            try: pass
            finally: cm.__exit__()

    def calibrate(self):

        cm = self.ContextManager()

        for i in xrange(self.rounds):
            pass


class WithRaiseExcept(Test):

    version = 2.0
    operations = 2 + 3 + 3
    rounds = 100000

    class BlockExceptions(object):
        def __enter__(self):
            pass
        def __exit__(self, exc, val, tb):
            return True

    def test(self):

        error = ValueError
        be = self.BlockExceptions()

        for i in xrange(self.rounds):
            with be: raise error
            with be: raise error
            with be: raise error,"something"
            with be: raise error,"something"
            with be: raise error,"something"
            with be: raise error("something")
            with be: raise error("something")
            with be: raise error("something")

    def calibrate(self):

        error = ValueError
        be = self.BlockExceptions()

        for i in xrange(self.rounds):
            pass
