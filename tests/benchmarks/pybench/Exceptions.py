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
