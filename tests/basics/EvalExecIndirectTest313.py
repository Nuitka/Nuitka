#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test indirect "eval" and "exec" calls from compiled frames."""

import builtins
import inspect


def call(convert, *args, **kwargs):
    return convert(*args, **kwargs)


def eval_indirect():
    return call(eval, "1+1")


def eval_keywords():
    return call(eval, "3+3", globals={})


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


print("eval", eval_indirect())
print("eval-keywords", eval_keywords())
print("exec", exec_indirect())
print("exec-defaults", exec_indirect_defaults())
print("frame-builtins", frame_builtins())
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
