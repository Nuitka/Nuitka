#     Copyright 2018, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" For enhanced bug reporting, these exceptions should be used.

They ideally should point out what it ought to take for reproducing the
issue when output.

"""

class NuitkaErrorBase(Exception):
    pass


class NuitkaNodeError(NuitkaErrorBase):

    # Try to output more information about nodes passed.
    def __str__(self):
        from nuitka.codegen.Indentation import indented

        parts = [""]

        for arg in self.args:
            if hasattr(arg, "asXmlText"):
                parts.append(indented("\n%s\n" % arg.asXmlText()))
            else:
                parts.append(arg)

        parts.append("")
        parts.append("The above information should be included in a bug report.")

        return '\n'.join(parts)


class NuitkaOptimizationError(NuitkaNodeError):
    pass


class NuitkaAssumptionError(AssertionError):
    pass
