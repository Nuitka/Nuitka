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
""" Progressbar for Scons compilation part.

This does only the interfacing with tracing and collection of information.

"""


from nuitka.Tracing import (
    closeProgressBar,
    enableProgressBar,
    reportProgressBar,
)

_total_files = None


def enableSconsProgressBar():
    enableProgressBar()

    def _closeSconsProgressBar():
        closeProgressBar()

    import atexit

    atexit.register(_closeSconsProgressBar)


def setSconsProgressBarTotal(total):

    global _total_files  # Singleton, pylint: disable=global-statement
    _total_files = total

    reportProgressBar(
        stage="Backend C", unit="file", item=None, total=_total_files, update=False
    )


def updateSconsProgressBar():
    reportProgressBar(
        stage="Backend C", unit="file", item=None, total=_total_files, update=True
    )
