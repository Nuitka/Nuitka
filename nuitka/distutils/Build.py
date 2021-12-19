#     Copyright 2021, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Nuitka python -m build integration """

import contextlib

import setuptools.build_meta

if not hasattr(setuptools.build_meta, "suppress_known_deprecation"):

    @contextlib.contextmanager
    def suppress_known_deprecation():
        yield

else:
    suppress_known_deprecation = setuptools.build_meta.suppress_known_deprecation


class NuitkaBuildMetaBackend(setuptools.build_meta._BuildMetaBackend):
    def build_wheel(
        self, wheel_directory, config_settings=None, metadata_directory=None
    ):
        with suppress_known_deprecation():
            return self._build_with_temp_dir(
                ["bdist_nuitka"], ".whl", wheel_directory, config_settings
            )


_BACKEND = NuitkaBuildMetaBackend()

get_requires_for_build_wheel = _BACKEND.get_requires_for_build_wheel
get_requires_for_build_sdist = _BACKEND.get_requires_for_build_sdist
prepare_metadata_for_build_wheel = _BACKEND.prepare_metadata_for_build_wheel
build_wheel = _BACKEND.build_wheel
build_sdist = _BACKEND.build_sdist
