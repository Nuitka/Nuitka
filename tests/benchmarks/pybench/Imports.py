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

# First imports:
import os
import package.submodule

class SecondImport(Test):

    version = 2.0
    operations = 5 * 5
    rounds = 40000

    def test(self):

        for i in xrange(self.rounds):
            import os
            import os
            import os
            import os
            import os

            import os
            import os
            import os
            import os
            import os

            import os
            import os
            import os
            import os
            import os

            import os
            import os
            import os
            import os
            import os

            import os
            import os
            import os
            import os
            import os

    def calibrate(self):

        for i in xrange(self.rounds):
            pass


class SecondPackageImport(Test):

    version = 2.0
    operations = 5 * 5
    rounds = 40000

    def test(self):

        for i in xrange(self.rounds):
            import package
            import package
            import package
            import package
            import package

            import package
            import package
            import package
            import package
            import package

            import package
            import package
            import package
            import package
            import package

            import package
            import package
            import package
            import package
            import package

            import package
            import package
            import package
            import package
            import package

    def calibrate(self):

        for i in xrange(self.rounds):
            pass

class SecondSubmoduleImport(Test):

    version = 2.0
    operations = 5 * 5
    rounds = 40000

    def test(self):

        for i in xrange(self.rounds):
            import package.submodule
            import package.submodule
            import package.submodule
            import package.submodule
            import package.submodule

            import package.submodule
            import package.submodule
            import package.submodule
            import package.submodule
            import package.submodule

            import package.submodule
            import package.submodule
            import package.submodule
            import package.submodule
            import package.submodule

            import package.submodule
            import package.submodule
            import package.submodule
            import package.submodule
            import package.submodule

            import package.submodule
            import package.submodule
            import package.submodule
            import package.submodule
            import package.submodule

    def calibrate(self):

        for i in xrange(self.rounds):
            pass
