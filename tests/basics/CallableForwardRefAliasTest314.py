#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test Callable aliases that embed annotationlib.ForwardRef values."""

from __future__ import annotations

from collections.abc import Callable


class CMapDecoder:
    pass


CMapResourceResolver = Callable[
    [str], bytes | bytearray | memoryview | "CMapDecoder" | None
]

print("Alias:", CMapResourceResolver)

union_value = CMapResourceResolver.__args__[1]
print("Union:", union_value)

forward_ref = union_value.__args__[3]
print(
    "ForwardRef:",
    (
        forward_ref.__forward_arg__,
        forward_ref.__forward_module__,
        forward_ref.__forward_is_class__,
    ),
)

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
