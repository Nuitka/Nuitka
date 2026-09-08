#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Float expression trees and controls with runtime-dependent inputs."""

import itertools
import sys


def shortChain(seed, repetitions):
    value = 1.5 if seed else 2.5

    for _unused in itertools.repeat(None, repetitions):
        value = (value + 1.25) * 0.5 - 0.125

    return value


def balancedTree(seed, repetitions):
    result = 0.0

    for _unused in itertools.repeat(None, repetitions):
        value = 1.5 if seed else 2.5
        factor = 0.625 if seed else 0.375
        result = (value + 1.25) * (factor - 0.125)
        seed = result < 1.0

    return result


def boxedRecurrence(seed, repetitions):
    value = 1.5 if seed else 2.5

    for _unused in itertools.repeat(None, repetitions):
        value = value + 1.25
        value = value * 0.5
        value = value - 0.125

    return value


def singleOperation(seed, repetitions):
    value = 1.5 if seed else 2.5

    for _unused in itertools.repeat(None, repetitions):
        value = value + 0.125

    return value


def unknownOperands(value, repetitions):
    for _unused in itertools.repeat(None, repetitions):
        value = (value + 1.25) * 0.5 - 0.125

    return value


operations = {
    "short_chain": boxedRecurrence,
    "balanced_tree": balancedTree,
    "boxed_recurrence": boxedRecurrence,
    "single_operation": singleOperation,
    "unknown_operands": unknownOperands,
}

# construct_begin
operations["short_chain"] = shortChain
# construct_end

operation_name = sys.argv[1] if len(sys.argv) > 1 else "short_chain"
repetition_count = int(sys.argv[2]) if len(sys.argv) > 2 else 50000
initial_value = float(sys.argv[3]) if len(sys.argv) > 3 else 1.5

result = operations[operation_name](initial_value, repetition_count)

print(repr(result))

#     Python test originally created or extracted from other peoples work. The
#     parts from me are licensed as below. It is at least Free Software where
#     it's copied from other people. In these cases, that will normally be
#     indicated.
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
