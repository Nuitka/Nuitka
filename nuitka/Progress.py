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
""" Progress bars in Nuitka.

This is responsible for wrapping the rendering of progress bar and emitting tracing
to the user while it's being displayed.

"""

from nuitka import Tracing
from nuitka.utils.ThreadedExecutor import RLock

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None
else:
    tqdm.set_lock(RLock())


class NuitkaProgessBar(object):
    def __init__(self, stage, total, unit):
        self.stage = stage
        self.total = total
        self.unit = unit

        # No item under work yet.
        self.item = None

        # No progress yet.
        self.progress = 0

        # Render immediately with 0 progress.
        self._reinit()

    def _reinit(self):
        # Note: Setting disable=None enables tty detection.
        self.tqdm = tqdm(
            initial=self.progress,
            total=self.total,
            unit=self.unit,
            disable=None,
            leave=False,
        )

        self.tqdm.set_description(self.stage)
        self.setCurrent(self.item)

    def updateTotal(self, total):
        if total != self.total:
            self.total = self.tqdm.total = total

    def setCurrent(self, item):
        if item != self.item:
            self.item = item

            if item is not None:
                self.tqdm.set_postfix(item=item)
            else:
                self.tqdm.set_postfix()

    def update(self):
        self.progress += 1
        self.tqdm.update(1)

    def clear(self):
        self.tqdm.clear()

    def hideProgressBar(self):
        # TODO: Need a better way to do this.
        self.tqdm.clear()

    def resumeProgressBar(self):
        self._reinit()

    def close(self):
        self.tqdm.close()


# Written by enableProgressBar from nuitka.options or Scons files in their processes.
use_progress_bar = False


def enableProgressBar():
    global use_progress_bar  # singleton, pylint: disable=global-statement

    # Tolerate the absence for now and ignore the progress bar
    if tqdm is not None:
        use_progress_bar = True


def setupProgressBar(stage, unit, total):
    # Make sure the other was closed.
    assert Tracing.progress is None

    if use_progress_bar:
        Tracing.progress = NuitkaProgessBar(
            stage=stage,
            total=total,
            unit=unit,
        )


def reportProgressBar(item, total=None, update=True):
    if Tracing.progress is not None:
        if total is not None:
            Tracing.progress.updateTotal(total)

        Tracing.progress.setCurrent(item)

        if update:
            Tracing.progress.update()


def closeProgressBar():
    """ Close the active progress bar. """

    if Tracing.progress is not None:
        Tracing.progress.close()
        Tracing.progress = None
