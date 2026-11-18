#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test "eval" and "exec" built-ins and "locals()" snapshot behavior."""

import builtins
import inspect
import sys


def call(convert, *args, **kwargs):
    return convert(*args, **kwargs)


def eval_indirect():
    return call(eval, "1+1")


def eval_keywords():
    if sys.version_info >= (3, 13):
        return call(eval, "3+3", globals={})

    return "not supported"


def exec_indirect():
    namespace = {}

    call(exec, "value = 6*7", namespace)

    return namespace["value"]


def exec_indirect_defaults():
    call(exec, "pass")

    return "ok"


def frame_builtins():
    value = 1

    builtins.locals()
    builtins.vars()
    builtins.dir()

    return "ok"


def snapshot():
    x = 1
    first = locals()
    second = locals()
    first["y"] = 2
    first["x"] = 3

    return first is second, "y" in locals(), locals()["x"], x


def late_assignment():
    x = 1
    first = locals()
    y = 2

    return sorted(first), sorted(locals())


def exec_implicit():
    x = 1
    exec("y = 2")

    return sorted(locals())


def eval_implicit():
    x = 21

    return eval("x * 2"), sorted(locals())


def vars_snapshot():
    x = 1
    first = vars()
    second = vars()
    first["y"] = 2

    return first is second, "y" in vars()


print("eval", eval_indirect())
print("eval-keywords", eval_keywords())
print("exec", exec_indirect())
print("exec-defaults", exec_indirect_defaults())
print("frame-builtins", frame_builtins())
print("snapshot", snapshot())
print("late-assignment", late_assignment())
print("exec-implicit", exec_implicit())
print("eval-implicit", eval_implicit())
print("vars-snapshot", vars_snapshot())

# Python 3.4 builtins lack '__text_signature__', so 'inspect.signature' raises
# ValueError for them.
if sys.version_info >= (3, 5):
    print("eval-signature", inspect.signature(eval))
    print("exec-signature", inspect.signature(exec))
    print("locals-signature", inspect.signature(locals))

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
