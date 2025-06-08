#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Progress bars in Nuitka.

This is responsible for wrapping the rendering of progress bar and emitting tracing
to the user while it's being displayed.

"""

from contextlib import contextmanager

from nuitka import Tracing
from nuitka.PythonVersions import isPythonWithGil
from nuitka.Tracing import general
from nuitka.utils.Importing import importFromInlineCopy
from nuitka.utils.ThreadedExecutor import RLock
from nuitka.utils.Utils import isWin32Windows

# spell-checker: ignore tqdm,ncols

# Late import and optional to be there.
use_progress_bar = False
_tqdm = None
_colorama = None

_uses_threading = False


def enableThreading():
    """Inform about threading being used."""

    # Singleton, pylint: disable=global-statement
    global _uses_threading

    _uses_threading = True


class NuitkaProgressBar(object):
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
        return _rich_progress


def enableProgressBar():
    global use_progress_bar  # singleton, pylint: disable=global-statement
    global _colorama  # singleton, pylint: disable=global-statement

    if _getTqdmModule() is not None:
        use_progress_bar = True

        if isWin32Windows():
            if _colorama is None:
                _colorama = importFromInlineCopy(
                    "colorama", must_exist=True, delete_module=True
                )

            _colorama.init()


def setupProgressBar(stage, unit, total, min_total=0):
    # Make sure the other was closed.
    assert Tracing.progress is None

    if use_progress_bar:
        Tracing.progress = NuitkaProgressBar(
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
    if _tqdm is None:
        return iterable
    else:
        result = NuitkaProgressBar(
            iterable=iterable, unit=unit, stage=stage, total=None, min_total=None
        )

        Tracing.progress = result

        return result


@contextmanager
def withNuitkaDownloadProgressBar(*args, **kwargs):
    if not use_progress_bar or (_getRichModule() is None and _getTqdmModule() is None):
        yield None
        return

    if _rich_progress:
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
        )

        with _rich_progress_cm as rich_p_instance:
            task_id = rich_p_instance.add_task(
                description, total=total_size_bytes or None
            )

            def onProgressRich(block_num=1, block_size=1, total_size=None):
                if total_size is not None:
                    rich_p_instance.update(task_id, total=total_size)

                current_completed = block_num * block_size
                rich_p_instance.update(task_id, completed=current_completed)

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


assert _getRichModule()

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
