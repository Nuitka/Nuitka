#!/usr/bin/env python
#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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

from __future__ import print_function

import sys

from redbaron import RedBaron

print("Updating", sys.argv[1])

with open(sys.argv[1], "r") as source_code:
    red = RedBaron(source_code.read().rstrip()+"\n")

def updateCall(call_node):
    max_len = 0
    for argument in call_node:
        if argument.type == "argument_generator_comprehension":
            return

        if argument.target is not None:
            key = argument.target.value
        else:
            key = None

        if key is not None:
            max_len = max(max_len, len(key))

    if "\n" not in call_node.second_formatting.dumps():
        del call_node.second_formatting[:]
        del call_node.third_formatting[:]

    for argument in call_node:
        if argument.target is not None:
            key = argument.target.value
        else:
            key = None

        if key is not None:
            if not argument.second_formatting:
                argument.second_formatting = " "

            if "\n" in str(call_node.second_formatting):
                if len(argument.first_formatting) > 0:
                    spacing = argument.first_formatting[0].value
                else:
                    spacing = ""

                if len(key)+len(spacing) != max_len + 1:
                    argument.first_formatting = " " * (max_len - len(key) + 1)
            else:
                argument.first_formatting = " "
        else:
            if "\n" not in str(call_node.second_formatting):
                if argument.value.type in ("string", "binary_string", "raw_string"):
                    argument.value.second_formatting = ""

def updateTuple(tuple_node):
    if "\n" not in str(tuple_node.dumps()):
        tuple_node.second_formatting = ""
        tuple_node.third_formatting = ""

        if tuple_node.with_parenthesis:
            if len(tuple_node.value.node_list) > 0:
                tuple_node.value.node_list[-1].second_formatting = ""

        for argument in tuple_node.value:
            if argument.type in ("string", "binary_string", "raw_string"):
                argument.second_formatting = ""


for node in red.find_all("CallNode"):
    try:
        updateCall(node)
    except Exception:
        print("Problem with", node)
        node.help(deep = True, with_formatting = True)
        raise

for node in red.find_all("TupleNode"):
    try:
        updateTuple(node)
    except Exception:
        print("Problem with", node)
        node.help(deep = True, with_formatting = True)
        raise

for node in red.find_all("ListNode"):
    try:
        updateTuple(node)
    except Exception:
        print("Problem with", node)
        node.help(deep = True, with_formatting = True)
        raise

with open(sys.argv[1], "w") as source_code:
    source_code.write(red.dumps())

