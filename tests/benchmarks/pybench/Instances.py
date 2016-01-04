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

class CreateInstances(Test):

    version = 2.0
    operations = 3 + 7 + 4
    rounds = 80000

    def test(self):

        class c:
            pass

        class d:
            def __init__(self,a,b,c):
                self.a = a
                self.b = b
                self.c = c

        class e:
            def __init__(self,a,b,c=4):
                self.a = a
                self.b = b
                self.c = c
                self.d = a
                self.e = b
                self.f = c

        for i in xrange(self.rounds):
            o = c()
            o1 = c()
            o2 = c()
            p = d(i,i,3)
            p1 = d(i,i,3)
            p2 = d(i,3,3)
            p3 = d(3,i,3)
            p4 = d(i,i,i)
            p5 = d(3,i,3)
            p6 = d(i,i,i)
            q = e(i,i,3)
            q1 = e(i,i,3)
            q2 = e(i,i,3)
            q3 = e(i,i)

    def calibrate(self):

        class c:
            pass

        class d:
            def __init__(self,a,b,c):
                self.a = a
                self.b = b
                self.c = c

        class e:
            def __init__(self,a,b,c=4):
                self.a = a
                self.b = b
                self.c = c
                self.d = a
                self.e = b
                self.f = c

        for i in xrange(self.rounds):
            pass
