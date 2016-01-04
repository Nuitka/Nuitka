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


def tupleWork():
    t = (1,2,3,4,5,6)

    a,b,c,d,e,f = t
    a,b,c,d,e,f = t
    a,b,c,d,e,f = t

    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]

    l = list(t)
    t = tuple(l)

    t = (1,2,3,4,5,6)

    a,b,c,d,e,f = t
    a,b,c,d,e,f = t
    a,b,c,d,e,f = t

    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]

    l = list(t)
    t = tuple(l)

    t = (1,2,3,4,5,6)

    a,b,c,d,e,f = t
    a,b,c,d,e,f = t
    a,b,c,d,e,f = t

    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]

    l = list(t)
    t = tuple(l)

    t = (1,2,3,4,5,6)

    a,b,c,d,e,f = t
    a,b,c,d,e,f = t
    a,b,c,d,e,f = t

    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]

    l = list(t)
    t = tuple(l)

    t = (1,2,3,4,5,6)

    a,b,c,d,e,f = t
    a,b,c,d,e,f = t
    a,b,c,d,e,f = t

    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]
    a,b,c = t[:3]

    l = list(t)
    t = tuple(l)

def run():
    for i in range(10000):
        tupleWork()

run()
