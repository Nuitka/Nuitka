# -*- coding: utf-8 -*-
#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


print "Hello World from module main code"


def printHelloWorld():
    print "Hello World from function main code"


print printHelloWorld

printHelloWorld()


def printHelloWorld2(arg):
    print arg


print printHelloWorld2

printHelloWorld2("Hello World from function positional argument")
printHelloWorld2(arg="Hello World from function keyword argument")


def printHelloWorld3(arg="Hello World from function default argument"):
    print arg


print printHelloWorld3

printHelloWorld3()

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
