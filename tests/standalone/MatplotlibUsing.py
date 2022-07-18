#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
#
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
#
""" Test using matplotlib, should actually do something with it. """

import matplotlib  # pylint:disable=unused-import

# nuitka-skip-unless-imports: matplotlib

# nuitka-project: --standalone

# Make sure, the usual bad ones are not included with anti-bloat.

# nuitka-project: --noinclude-setuptools-mode=error
# nuitka-project: --noinclude-pytest-mode=error
# nuitka-project: --noinclude-custom-mode=numpy.distutils:error
# nuitka-project: --noinclude-custom-mode=IPython:error

print("OK.")