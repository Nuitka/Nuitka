#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Python tests originally created or extracted from other peoples work. The
#     parts were too small to be protected.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#
class W1(object):
    def __init__(self):
        self.__hidden = 5


class W2(object):
    __slots__ = ["__hidden"]

    def __init__(self):
        self.__hidden = 5


class _W1(object):
    def __init__(self):
        self.__hidden = 5


class _W2(object):
    __slots__ = ["__hidden"]

    def __init__(self):
        self.__hidden = 5


class a_W1(object):
    def __init__(self):
        self.__hidden = 5


class a_W2(object):
    __slots__ = ["__hidden"]

    def __init__(self):
        self.__hidden = 5


class W1_(object):
    def __init__(self):
        self.__hidden = 5


class W2_(object):
    __slots__ = ["__hidden"]

    def __init__(self):
        self.__hidden = 5


for w in (W1, W2, _W1, _W2, a_W1, a_W2, W1_, W2_):
    try:
        print(w)
        print(dir(w))
        a = w()
    except AttributeError:
        print("bug in %s" % w)
