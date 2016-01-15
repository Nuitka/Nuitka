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


def someFunction(rounds):
    # define functions
    def f(a,b,c,d = 1,e = 2,f = 3):
        return f

    args = 1,2
    kwargs = dict(c = 3,d = 4,e = 5)

    # do calls
    for i in xrange(rounds):
        f(a = i,b = i,c = i)
        f(f = i,e = i,d = i,c = 2,b = i,a = 3)
        f(1,b = i,**kwargs)
        f(*args,**kwargs)

        f(a = i,b = i,c = i)
        f(f = i,e = i,d = i,c = 2,b = i,a = 3)
        f(1,b = i,**kwargs)
        f(*args,**kwargs)

        f(a = i,b = i,c = i)
        f(f = i,e = i,d = i,c = 2,b = i,a = 3)
        f(1,b = i,**kwargs)
        f(*args,**kwargs)

        f(a = i,b = i,c = i)
        f(f = i,e = i,d = i,c = 2,b = i,a = 3)
        f(1,b = i,**kwargs)
        f(*args,**kwargs)

        f(a = i,b = i,c = i)
        f(f = i,e = i,d = i,c = 2,b = i,a = 3)
        f(1,b = i,**kwargs)
        f(*args,**kwargs)

someFunction(10000);
