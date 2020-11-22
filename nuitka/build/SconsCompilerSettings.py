#     Copyright 2020, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" This contains the tuning of the compilers towards defined goals.

"""


def enableC11Settings(env, clangcl_mode, msvc_mode, clang_mode, gcc_mode, gcc_version):
    if clangcl_mode:
        c11_mode = True
    elif msvc_mode:
        c11_mode = False
    elif clang_mode:
        c11_mode = True
    elif gcc_mode and gcc_version >= (5,):
        c11_mode = True
    else:
        c11_mode = False

    if c11_mode:
        if gcc_mode:
            env.Append(CCFLAGS=["-std=c11"])
        elif msvc_mode:
            env.Append(CCFLAGS=["/std:c11"])

    return c11_mode
