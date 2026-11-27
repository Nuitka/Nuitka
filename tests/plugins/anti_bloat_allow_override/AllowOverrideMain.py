#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Test that an 'allow' value overrides a no-auto-follow rule from a parent package."""

# nuitka-project: --mode=standalone
# nuitka-project: --user-package-configuration-file={MAIN_DIRECTORY}/test_case.nuitka-package.config.yml

import allow_override_package.child

print(allow_override_package.child.VALUE)
print(allow_override_package.child.NARROW_BROAD)

if allow_override_package.child.NARROW_SPECIFIC is None:
    print("narrow suppression works")
else:
    print("narrow value %s" % allow_override_package.child.NARROW_SPECIFIC)

try:
    import allow_override_package.sibling
except ImportError:
    print("suppression works")
else:
    print("suppression failed")

# nuitka-test-compiled-only:stdout: suppression works
# nuitka-test-uncompiled-only:stdout: suppression failed
# nuitka-test-compiled-only:stdout: narrow suppression works
# nuitka-test-uncompiled-only:stdout: narrow value 126

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
