#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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
