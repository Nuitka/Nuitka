#!/usr/bin/env python
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

from __future__ import print_function

import os
import re
import shutil
import sys

from redbaron import RedBaron  # @UnresolvedImport

print("Consider", sys.argv[1], end = ": ")

old_code = open(sys.argv[1], 'r').read()

red = RedBaron(old_code.rstrip()+'\n')

def updateCall(call_node):
    max_len = 0
    for argument in call_node:
        if argument.type == "argument_generator_comprehension":
            return

        if hasattr(argument, "target") and argument.target is not None:
            key = argument.target.value
        else:
            key = None

        if key is not None:
            max_len = max(max_len, len(key))

    if '\n' not in call_node.second_formatting.dumps():
        del call_node.second_formatting[:]
        del call_node.third_formatting[:]

    for argument in call_node:
        if hasattr(argument, "target") and argument.target is not None:
            key = argument.target.value
        else:
            key = None

        if key is not None:
            if not argument.second_formatting:
                argument.second_formatting = ' '

            if '\n' in str(call_node.second_formatting):
                if len(argument.first_formatting) > 0:
                    spacing = argument.first_formatting[0].value
                else:
                    spacing = ""

                if len(key)+len(spacing) != max_len + 1:
                    argument.first_formatting = ' ' * (max_len - len(key) + 1)
            else:
                argument.first_formatting = ' '
        else:
            if '\n' not in str(call_node.second_formatting):
                if argument.value.type in ("string", "binary_string", "raw_string"):
                    argument.value.second_formatting = ""

def updateTuple(tuple_node):
    if '\n' not in str(tuple_node.dumps()):
        tuple_node.second_formatting = ""
        tuple_node.third_formatting = ""

        if tuple_node.type == "tuple" and tuple_node.with_parenthesis:
            if len(tuple_node.value.node_list) > 0:
                tuple_node.value.node_list[-1].second_formatting = ""

        for argument in tuple_node.value:
            if argument.type in ("string", "binary_string", "raw_string"):
                argument.second_formatting = ""

def updateString(string_node):
    # Skip doc strings for now.
    if not hasattr( node.parent, "type") or \
       string_node.parent.type in ("class", "def", None):
        return

    value = string_node.value

    def isQuotedWith(quote):
        return value.startswith(quote) and value.endswith(quote)

    for quote in "'''", '"""', "'", '"':
        if isQuotedWith(quote):
            break
    else:
        assert False, value

    real_value = value[len(quote):-len(quote)]
    assert quote + real_value + quote == value

    if '\n' not in real_value:
        # Single characters, should be quoted with "'"
        if len(eval(value)) == 1:
            if real_value != "'":
                string_node.value = "'" + real_value + "'"
        else:
            if '"' not in real_value:
                string_node.value = '"' + real_value + '"'

def updateDefNode(def_node):
    # This is between "def" and function name.
    def_node.first_formatting = ' '

    # This is after the opening/closing brace, we don't want it there.
    def_node.third_formatting = ""
    def_node.fourth_formatting = ""

    # This is to insert/remove spaces or new lines, depending on line length
    # so far, but is not functional at all.
    for argument_node in def_node.arguments:
        argument_node.first_formatting = ' '
        argument_node.second_formatting = ' '

def updateCommentNode(comment_node):

    if "pylint:" in str(comment_node.value):
        def replacer(part):
            return part.group(1) + ','.join(sorted(part.group(2).split(',')))

        new_value = re.sub(r"(pylint\: disable=)(.*)", replacer, str(comment_node.value), flags = re.M)
        comment_node.value = new_value

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

for node in red.find_all("StringNode"):
    try:
        updateString(node)
    except Exception:
        print("Problem with", node)
        node.help(deep = True, with_formatting = True)
        raise

for node in red.find_all("DefNode"):
    try:
        updateDefNode(node)
    except Exception:
        print("Problem with", node)
        node.help(deep = True, with_formatting = True)
        raise

for node in red.find_all("CommentNode"):
    try:
        updateCommentNode(node)
    except Exception:
        print("Problem with", node)
        node.help(deep = True, with_formatting = True)
        raise

if False:
    while len(red) > 2 and red[0].type == "string" and red[1].type == "endl" and red[2].type == "endl":
        del red[1]


new_code = red.dumps()

if new_code != old_code:

    new_name = sys.argv[1] + ".new"

    with open(new_name, 'w') as source_code:
        source_code.write(red.dumps())

    # There is no way to safely replace a file on Windows, but lets try on Linux
    # at least.
    old_stat = os.stat(sys.argv[1])

    try:
        os.rename(new_name, sys.argv[1])
    except OSError:
        shutil.copy(new_name, sys.argv[1])

    os.chmod(sys.argv[1], old_stat.st_mode)

    print("updated.")
else:
    print("OK.")
