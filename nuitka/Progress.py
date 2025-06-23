#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Progress bars in Nuitka.

This is responsible for wrapping the rendering of progress bar and emitting tracing
to the user while it's being displayed.

"""

import atexit
import sys
from contextlib import contextmanager

from nuitka import Tracing
from nuitka.PythonVersions import isPythonWithGil
from nuitka.Tracing import general
from nuitka.utils.Importing import importFromInlineCopy
from nuitka.utils.ThreadedExecutor import RLock
from nuitka.utils.Utils import isWin32Windows, withNoExceptions

# spell-checker: ignore tqdm,ncols

# Late import and optional to be there.
use_progress_bar = "none"
_tqdm = None
_colorama = None

# Determine the bullet character based on file encoding
try:
    "\u2022".encode(sys.__stdout__.encoding)
    _bullet_character = "\u2022"
except UnicodeEncodeError:
    _bullet_character = "*"

_uses_threading = False


def enableThreading():
    """Inform about threading being used."""

    # Singleton, pylint: disable=global-statement
    global _uses_threading

    _uses_threading = True


class NuitkaProgressBarTqdm(object):
    def __init__(self, iterable, stage, total, min_total, unit):
        self.total = total

        # The minimum may not be provided, then default to 0.
        self.min_total = min_total

        # No item under work yet.
        self.item = None

        # No progress yet.
        self.progress = 0

        # Render immediately with 0 progress, and setting disable=None enables tty detection.
        self.tqdm = _tqdm(
            iterable=iterable,
            initial=self.progress,
            total=(
                max(self.total, self.min_total) if self.min_total is not None else None
            ),
            unit=unit,
            disable=None,
            leave=False,
            dynamic_ncols=True,
            bar_format="{desc}{percentage:3.1f}%|{bar:25}| {n_fmt}/{total_fmt}{postfix}",
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
        # spell-checker: ignore nolock
        with self.tqdm.external_write_mode(
            nolock=not _uses_threading or isPythonWithGil()
        ):
            yield


class NuitkaProgressBarRich(object):
    def __init__(self, iterable, stage, total, min_total, unit):
        self.iterable = iterable

        if total is None and hasattr(iterable, "__len__"):
            self.total = len(iterable)
        else:
            self.total = total

        self.min_total = min_total
        self.item = None

        self.rich_progress = _rich_progress.Progress(
            _rich_progress.TextColumn("[bold blue]{task.description}", justify="right"),
            _rich_progress.BarColumn(bar_width=25),
            _rich_progress.TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
            _bullet_character,
            _rich_progress.TextColumn(
                "{task.completed:>0.0f}/{task.total:>0.0f} {task.fields[unit_label]}"
            ),
            _rich_progress.TextColumn("{task.fields[postfix_bullet]}"),
            _rich_progress.TextColumn("[bold blue]{task.fields[postfix]}"),
            refresh_per_second=10000,
            transient=True,
            redirect_stdout=False,
            redirect_stderr=False,
        )
        self.rich_progress.start()

        effective_total = self.total
        if self.total is not None:
            if self.min_total is not None:
                effective_total = max(self.total, self.min_total)
            else:
                effective_total = max(self.total, 0)
        elif self.min_total is not None and self.min_total > 0:
            effective_total = self.min_total
        else:
            effective_total = None

        self.task_id = self.rich_progress.add_task(
            description=stage,
            total=effective_total,
            postfix="",
            postfix_bullet="",
            unit_label=unit or "",
            start=True,
        )
        self.setCurrent(self.item)

    def __iter__(self):
        if self.iterable is None:
            return iter([])
        else:
            self.rich_progress.start_task(self.task_id)
            for val in self.iterable:
                yield val
                self.update()

    def updateTotal(self, total):
        if total != self.total:
            self.total = total
            effective_total = total
            if self.min_total is not None:
                effective_total = max(total, self.min_total)
            self.rich_progress.update(self.task_id, total=effective_total)

    def setCurrent(self, item):
        if item != self.item:
            self.item = item

            self.rich_progress.update(
                self.task_id,
                postfix=str(item),
                postfix_bullet=_bullet_character if item is not None else "",
            )

    def update(self):
        self.rich_progress.update(self.task_id, advance=1)

    def clear(self):
        # Rich progress with transient=True clears on stop, so this is not
        # needed.
        pass

    def close(self):
        if self.rich_progress.live.is_started:
            # Ensure task is marked as finished if not already
            if (
                self.task_id in self.rich_progress.task_ids
                and not self.rich_progress.tasks[
                    self.rich_progress.task_ids.index(self.task_id)
                ].finished
            ):

                with withNoExceptions():
                    self.rich_progress.stop_task(self.task_id)

            with withNoExceptions():
                self.rich_progress.stop()

    @contextmanager
    def withExternalWritingPause(self):
        # Temporarily stop (and clear due to transient=True) the Rich progress display
        # to allow external printing, then restart it.
        if self.rich_progress.live.is_started:
            self.rich_progress.stop()
            try:
                yield
            finally:
                self.rich_progress.start()
        else:
            yield


def _getTqdmModule():
    """Get the tqdm module if possible, might return None."""
    global _tqdm  # singleton, pylint: disable=global-statement

    if _tqdm:
        return _tqdm
    elif _tqdm is False:
        return None
    else:
        _tqdm = importFromInlineCopy("tqdm", must_exist=False, delete_module=True)

        if _tqdm is None:
            try:
                # Cannot use import tqdm due to pylint bug.
                import tqdm as tqdm_installed  # pylint: disable=I0021,import-error

                _tqdm = tqdm_installed
            except ImportError:
                # We handle the case without inline copy too, but it may be removed, e.g. on
                # Debian it's only a recommended install, and not included that way.
                pass

        if _tqdm is None:
            _tqdm = False
            return None

        _tqdm = _tqdm.tqdm

        # Tolerate the absence ignore the progress bar
        _tqdm.set_lock(RLock())

        return _tqdm


# Global variable to cache the rich module instance or import failure
_rich_progress = None


def _getRichModule():
    """Get the rich module if possible, might return None."""
    global _rich_progress  # singleton, pylint: disable=global-statement

    if _rich_progress:
        return _rich_progress
    elif _rich_progress is False:
        return None

    if _rich_progress is None:
        try:
            # Try importing from pip's vendored packages first
            import pip._vendor.rich.progress as vendored_rich_progress

            _rich_progress = vendored_rich_progress
        except ImportError:
            try:
                import rich.progress as standard_rich_progress

                _rich_progress = standard_rich_progress
            except ImportError:
                _rich_progress = False

        if not hasattr(_rich_progress, "Progress"):
            _rich_progress = False

    if _rich_progress is False:
        return None
    else:
        atexit.register(_cleanupRich)

        return _rich_progress


def enableProgressBar(progress_bar):
    global use_progress_bar  # singleton, pylint: disable=global-statement
    global _colorama  # singleton, pylint: disable=global-statement

    if progress_bar in ("rich", "auto"):
        if _getRichModule() is not None:
            use_progress_bar = "rich"

    # If selected, or if rich wasn't found.
    if progress_bar == "tqdm" or (
        progress_bar == "rich" and use_progress_bar == "none"
    ):
        if _getTqdmModule() is not None:
            use_progress_bar = "tqdm"

            if isWin32Windows():
                if _colorama is None:
                    _colorama = importFromInlineCopy(
                        "colorama", must_exist=True, delete_module=True
                    )

                _colorama.init()


def _cleanupRich():
    if use_progress_bar == "rich" and Tracing.progress is not None:
        with withNoExceptions():
            Tracing.progress.close()


def setupProgressBar(stage, unit, total, min_total=0):
    # Make sure the other was closed.
    assert Tracing.progress is None

    if use_progress_bar == "rich":
        Tracing.progress = NuitkaProgressBarRich(
            iterable=None,
            stage=stage,
            total=total,
            min_total=min_total,
            unit=unit,
        )
    elif use_progress_bar == "tqdm":
        Tracing.progress = NuitkaProgressBarTqdm(
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
        except Exception as e:  # Catch all the things, pylint: disable=broad-except
            # We disable the progress bar now, because it's causing issues.
            general.warning("Progress bar disabled due to bug: %s" % (str(e)))
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
    if use_progress_bar == "rich":
        result = NuitkaProgressBarRich(
            iterable=iterable, unit=unit, stage=stage, total=None, min_total=None
        )
        Tracing.progress = result
        return result
    elif use_progress_bar == "tqdm":
        result = NuitkaProgressBarTqdm(
            iterable=iterable, unit=unit, stage=stage, total=None, min_total=None
        )
        Tracing.progress = result
        return result
    else:
        return iterable


@contextmanager
def withNuitkaDownloadProgressBar(*args, **kwargs):
    if use_progress_bar == "none":
        yield None
        return

    # Check if stdout is a TTY for Rich
    is_tty = sys.stdout.isatty()

    if use_progress_bar == "rich":
        description = kwargs.get("desc", "Downloading")
        total_size_bytes = kwargs.get("total", 0)

        _rich_progress_cm = _rich_progress.Progress(
            _rich_progress.TextColumn("[bold blue]{task.description}", justify="right"),
            _rich_progress.BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "\u2022",
            _rich_progress.DownloadColumn(),
            "\u2022",
            _rich_progress.TransferSpeedColumn(),
            "\u2022",
            _rich_progress.TimeRemainingColumn(),
            transient=True,
            disable=not is_tty,
        )

        with _rich_progress_cm as rich_p_instance:
            task_id = rich_p_instance.add_task(
                description, total=total_size_bytes or None
            )

            def onProgressRich(block_num=1, block_size=1, total_size=None):
                # pylint: disable=unused-argument

                if total_size is not None:
                    rich_p_instance.update(task_id, total=total_size)

            yield onProgressRich
    else:

        class NuitkaDownloadProgressBarTqdm(_tqdm):
            # spell-checker: ignore bsize, tsize
            def onProgress(self, b=1, bsize=1, tsize=None):
                if tsize is not None:
                    self.total = tsize
                self.update(b * bsize - self.n)

        tqdm_kwargs = kwargs.copy()
        tqdm_kwargs.update(
            disable=None,
            leave=False,
            dynamic_ncols=True,
            bar_format="{desc} {percentage:3.1f}%|{bar:25}| {n_fmt}/{total_fmt}{postfix}",
        )
        with NuitkaDownloadProgressBarTqdm(*args, **tqdm_kwargs) as pb_tqdm:
            yield pb_tqdm.onProgress


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
