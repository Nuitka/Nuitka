#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


# nuitka-skip-unless-imports: numba

# nuitka-project: --mode=standalone
# nuitka-project: --enable-plugin=numba
# nuitka-project: --numba-enable-jit=yes

import numba
import numpy as np
from numba import njit, stencil


@njit(cache=True)
def imported_njit(a):
    return a.sum()


@numba.njit
def attribute_njit(a):
    return a.sum() + 1


@stencil
def stencil_kernel(a):
    return (a[0, 0] + a[1, 0] + a[0, 1] + a[-1, 0] + a[0, -1]) / 5


x = np.arange(100).reshape(10, 10).astype(np.float64)

print("imported njit", imported_njit(x))
print("attribute njit", attribute_njit(x))

out = np.empty_like(x)
print("stencil", stencil_kernel(x, out=out).sum())

print("OK.")

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
