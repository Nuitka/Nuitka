# -*- coding: utf-8 -*-
#     Copyright 2019, Kay Hayen, mailto:kay.hayen@gmail.com
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

# All of these should be identical with correct software behavior.

print "Output with newline."
print "Output", "with", "newline."
print "Output trailing spaces ", "with ", "newline."
print "Output ",
print "with ",
print "newline."
print "Output\twith tab"
print "Output\t",
print "with tab"

# These ones gave errors with previous literal bugs:
print "changed 2"
print "foo%sbar%sfred%sbob?????"

a = "partial print"
# b doesn't exist

try:
    print a, undefined_global  # @UndefinedVariable
except Exception, e:
    print "then occurred", repr(e)

print "No newline at the end",

x = 1
print """
New line is no soft space, is it
""", x
