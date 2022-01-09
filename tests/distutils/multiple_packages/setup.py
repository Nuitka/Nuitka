#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
from setuptools import setup

# This is a list of files to install, and where
# (relative to the 'root' dir, where setup.py is)
# You could be more specific.
setup(
    name="multiple_packages_example",
    version="101",
    packages=[
        "some_package",
        "some_package_a",
        "some_package_b",
        "other_package",
        "other_package_a",
    ],
    py_modules=["main_module"],
    scripts=["runner"],
    description="hello",
    author="Nobody really",
    author_email="email@someplace.com",
    url="whatever",
    long_description="""Really long text here.""",
)
