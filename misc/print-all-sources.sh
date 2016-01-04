#!/bin/sh
#     Copyright 2016, Kay Hayen, mailto:kay.hayen@gmail.com
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
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

cd `dirname $0`/..

find nuitka -name \*.py -a \! -path *inline_copy*
find bin -name \*.py
find nuitka/build/static_src -name \*.cpp
find nuitka/build/include -name \*.hpp
find nuitka/build/ -name \*.scons
find misc -name \*.sh
find bin -name \*.sh
echo Developer_Manual.rst
echo Changelog.rst
