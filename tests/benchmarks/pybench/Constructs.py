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
