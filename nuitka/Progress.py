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

from contextlib import contextmanager

from nuitka import Tracing
from nuitka.Tracing import general
from nuitka.utils.Importing import importFromInlineCopy
from nuitka.utils.ThreadedExecutor import RLock
from nuitka.utils.Utils import isWin32Windows

# Late import and optional to be there.
use_progress_bar = False
tqdm = None


class NuitkaProgessBar(object):
    def __init__(self, iterable, stage, total, min_total, unit):
        self.total = total

        # The minimum may not be provided, then default to 0.
        self.min_total = min_total

        # No item under work yet.
        self.item = None

        # No progress yet.
        self.progress = 0

        # Render immediately with 0 progress, and setting disable=None enables tty detection.
        self.tqdm = tqdm(
            iterable=iterable,
            initial=self.progress,
            total=max(self.total, self.min_total)
            if self.min_total is not None
            else None,
            unit=unit,
            disable=None,
            leave=False,
            bar_format="{desc}{percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}{postfix}",
        )

        self.tqdm.set_description(stage)
        self.setCurrent(self.item)

    def __iter__(self):
        return iter(self.tqdm)

    def updateTotal(self, total):
        if total != self.total:
            self.total = total
            self.tqdm.total = max(total, self.min_total)

    def setCurrent(self, item):
        if item != self.item:
            self.item = item

            if item is not None:
                self.tqdm.set_postfix_str(item)
            else:
                self.tqdm.set_postfix()

    def update(self):
        self.progress += 1
        self.tqdm.update(1)

    def clear(self):
        self.tqdm.clear()

    def close(self):
        self.tqdm.close()

    @contextmanager
    def withExternalWritingPause(self):
        with self.tqdm.external_write_mode():
            yield


def _getTqdmModule():
    global tqdm  # singleton, pylint: disable=global-statement

    if tqdm:
        return tqdm
    elif tqdm is False:
        return None
    else:
        tqdm = importFromInlineCopy("tqdm", must_exist=False)

        if tqdm is None:
            try:
                # Cannot use import tqdm due to pylint bug.
                import tqdm as tqdm_installed  # pylint: disable=I0021,import-error

                tqdm = tqdm_installed
            except ImportError:
                # We handle the case without inline copy too, but it may be removed, e.g. on
                # Debian it's only a recommended install, and not included that way.
                pass

        if tqdm is None:
            tqdm = False
            return None

        tqdm = tqdm.tqdm

        # Tolerate the absence ignore the progress bar
        tqdm.set_lock(RLock())

        return tqdm


def enableProgressBar():
    global use_progress_bar  # singleton, pylint: disable=global-statement

    if _getTqdmModule() is not None:
        use_progress_bar = True

        if isWin32Windows():
            colorama = importFromInlineCopy("colorama", must_exist=True)
            colorama.init()


def setupProgressBar(stage, unit, total, min_total=0):
    # Make sure the other was closed.
    assert Tracing.progress is None

    if use_progress_bar:
        Tracing.progress = NuitkaProgessBar(
            iterable=None,
            stage=stage,
            total=total,
            min_total=min_total,
            unit=unit,
        )


def reportProgressBar(item, total=None, update=True):
    if Tracing.progress is not None:
        try:
            if total is not None:
                Tracing.progress.updateTotal(total)

            Tracing.progress.setCurrent(item)

            if update:
                Tracing.progress.update()
        except Exception:  # Catch all the things, pylint: disable=broad-except
            # We disable the progress bar now, because it's causing issues.
            general.warning("Progress bar disabled due to bug")
            closeProgressBar()


def closeProgressBar():
    """Close the active progress bar.

    Returns: int or None - if displayed, the total used last time.
    """

    if Tracing.progress is not None:
        # Retrieve that previous total, for repeated progress bars, it
        # can be used as a new minimum.
        result = Tracing.progress.total

        Tracing.progress.close()
        Tracing.progress = None

        return result


def wrapWithProgressBar(iterable, stage, unit):
    if tqdm is None:
        return iterable
    else:
        result = NuitkaProgessBar(
            iterable=iterable, unit=unit, stage=stage, total=None, min_total=None
        )

        Tracing.progress = result

        return result
