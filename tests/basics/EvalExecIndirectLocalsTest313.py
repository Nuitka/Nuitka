#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-project: --experimental=force-locals-frame-proxy

"""Test indirect "eval" accessing locals of compiled frames."""

import builtins


def eval_local(convert):
    value = 21

    return convert("value * 2")


def exec_local(convert):
    value = 5

    convert("value = value + 1")

    return value


def frame_builtins():
    x = 1
    y = 2

    return sorted(builtins.locals()), sorted(builtins.vars()), builtins.dir()


print("eval-local", eval_local(eval))
print("exec-local", exec_local(exec))
print("frame-builtins", frame_builtins())

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
