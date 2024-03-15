#     Copyright 2024, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Tags and set of it.

Used by optimization to keep track of the current state of optimization, these
tags trigger the execution of optimization steps, which in turn may emit these
tags to execute other steps.

"""

allowed_tags = (
    # New code means new statements.
    # Could be an inlined exec statement.
    "new_code",
    # Added new import.
    "new_import",
    # New statements added, removed.
    "new_statements",
    # New expression added.
    "new_expression",
    # Loop analysis is incomplete, or only just now completed.
    "loop_analysis",
    # TODO: A bit unclear what this it, potentially a changed variable.
    "var_usage",
    # Detected module variable to be read only.
    "read_only_mvar",
    # Trusting module variables in functions.
    "trusted_module_variables",
    # New built-in reference detected.
    "new_builtin_ref",
    # New built-in call detected.
    "new_builtin",
    # New raise statement detected.
    "new_raise",
    # New constant introduced.
    "new_constant",
)


class TagSet(set):
    def onSignal(self, signal):
        if type(signal) is str:
            signal = signal.split()

        for tag in signal:
            self.add(tag)

    def check(self, tags):
        for tag in tags.split():
            assert tag in allowed_tags, tag

            if tag in self:
                return True
        return False

    def add(self, tag):
        assert tag in allowed_tags, tag

        set.add(self, tag)


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
