#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Progress bars in Nuitka.

This is responsible for wrapping the rendering of progress bar and emitting tracing
to the user while it's being displayed.

"""

import atexit
import sys
from contextlib import contextmanager

from nuitka import Tracing
from nuitka.Tracing import general, getDisableStylesCode
from nuitka.utils.Importing import importFromInlineCopy
from nuitka.utils.ThreadedExecutor import RLock
from nuitka.utils.Utils import isWin32Windows, withNoExceptions

# spell-checker: ignore tqdm,ncols

# Late import and optional to be there.
use_progress_bar = None
_tqdm = None
_colorama = None
_barflow = None


def wrapWithStyles(value, styles):
    if use_progress_bar == "tqdm":
        return Tracing.wrapWithStyles(value, styles)
    else:
        return "[%s]%s" % (" ".join(styles), value)


_uses_threading = False

_progress_info_style = ("bold", "blue")
_progress_percentage_style = ("bold", "green")


def enableThreading():
    """Inform about threading being used."""

    # Singleton, pylint: disable=global-statement
    global _uses_threading

    if not _uses_threading:
        # Install the redirection for stdout/stderr to ensure that partial lines
        # which are common for threaded tools do not get mixed with progress bar.

        if not hasattr(sys.stdout, "original_stream"):
            sys.stdout = Tracing.LineBufferedStreamRedirector(sys.stdout)

        if not hasattr(sys.stderr, "original_stream"):
            sys.stderr = Tracing.LineBufferedStreamRedirector(sys.stderr)

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

        bar_format = "%s%s|{bar:25}| {n_fmt}/{total_fmt}{unit}%s%s" % (
            wrapWithStyles("{desc}", styles=_progress_info_style),
            wrapWithStyles("{percentage:5.1f}%", styles=_progress_percentage_style),
            wrapWithStyles("{postfix}", styles=_progress_info_style),
            getDisableStylesCode(),
        )

        # Ensure we use the original stream for tqdm, so it doesn't trigger our redirection
        # which would cause infinite recursion.
        tqdm_file = sys.stderr
        if hasattr(tqdm_file, "original_stream"):
            tqdm_file = tqdm_file.original_stream

        # Render immediately with 0 progress, and setting disable=None enables tty detection.
        self.tqdm = _tqdm(
            iterable=iterable,
            initial=self.progress,
            total=(
                max(self.total, self.min_total) if self.min_total is not None else None
            ),
            unit=(" " + unit + "s") if unit else "",
            disable=None,
            leave=False,
            dynamic_ncols=True,
            bar_format=bar_format,
            file=tqdm_file,
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
        # We perform what "external_write_mode" does manually, so we can force the
        # refresh to happen, which it seemingly doesn't do reliably.

        # spell-checker: ignore nolock
        if _uses_threading:
            lock = self.tqdm.get_lock()
            lock.acquire()

        try:
            self.tqdm.clear(nolock=True)
            yield
            self.tqdm.refresh(nolock=True)
        finally:
            if _uses_threading:
                lock.release()


class NuitkaProgressBarRich(object):
    def __init__(self, iterable, stage, total, min_total, unit):
        self.iterable = iterable or ()

        if total is None and hasattr(iterable, "__len__"):
            self.total = len(iterable)
        else:
            self.total = total

        self.min_total = min_total
        self.item = None

        class TextColumnCropped(_rich_progress.TextColumn):
            def __init__(
                self,
                text_format,
                style="none",
                justify="left",
                markup=True,
                highlighter=None,
                table_column=None,
            ):
                # False alarm, pylint: disable=non-parent-init-called
                _rich_progress.TextColumn.__init__(
                    self,
                    text_format=text_format,
                    style=style,
                    justify=justify,
                    markup=markup,
                    highlighter=highlighter,
                    table_column=table_column,
                )

            def render(self, task):
                _text = self.text_format.format(task=task)
                if self.markup:
                    text = _rich_progress.Text.from_markup(
                        _text, style=self.style, justify=self.justify, overflow="crop"
                    )
                else:
                    text = _rich_progress.Text(
                        _text, style=self.style, justify=self.justify, overflow="crop"
                    )
                if self.highlighter:
                    self.highlighter.highlight(text)
                return text

        # Unwrap our own redirection for Scons.
        rich_file = sys.stdout
        if hasattr(rich_file, "original_stream"):
            rich_file = rich_file.original_stream

        # This is for "rich" to not use the "SconsStreamRedirector" that we install
        # for Scons, but instead use the one that really goes to the terminal.
        console = _rich_console.Console(file=rich_file)

        self.rich_progress = _rich_progress.Progress(
            _rich_progress.TextColumn(
                wrapWithStyles("{task.description}", styles=_progress_info_style),
                justify="full",
            ),
            _rich_progress.BarColumn(bar_width=25),
            _rich_progress.TextColumn(
                wrapWithStyles(
                    "{task.percentage:>5.1f}%", styles=_progress_percentage_style
                ),
                justify="full",
            ),
            "|",
            _rich_progress.TextColumn(
                "{task.completed:>0.0f}/{task.total:>0.0f}{task.fields[unit_label]}",
                justify="full",
            ),
            _rich_progress.TextColumn("{task.fields[postfix_bullet]}"),
            TextColumnCropped(
                wrapWithStyles("{task.fields[postfix]}", styles=_progress_info_style),
            ),
            refresh_per_second=10000,
            transient=True,
            redirect_stdout=False,
            redirect_stderr=False,
            console=console,
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
            unit_label=(" " + unit + "s") if unit else "",
            start=True,
        )
        self.setCurrent(self.item)

    def __iter__(self):
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
                postfix_bullet="|" if item is not None else "",
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
        was_started = self.rich_progress.live.is_started

        if was_started:
            self.rich_progress.stop()

        try:
            yield
        finally:
            if was_started:
                self.rich_progress.start()


class NuitkaProgressBarBarflow(object):
    def __init__(self, iterable, stage, total, min_total, unit):
        self.iterable = iterable or ()

        if total is None and hasattr(iterable, "__len__"):
            self.total = len(iterable)
        else:
            self.total = total

        self.min_total = min_total
        self.item = None
        # Current item is rendered by a trailing callback column, NOT folded
        # into the description — folding it in changes the description width
        # per module and shifts the whole bar sideways (a staircase). Keeping
        # the description fixed anchors the bar, exactly like tqdm's postfix.
        self._postfix = ""

        effective_total = self._effectiveTotal(self.total, self.min_total)

        # barflow renders on its own thread straight to stderr's file
        # descriptor, exactly like tqdm, so it must use the original stream
        # rather than Nuitka's redirector to avoid recursion. Auto-disable
        # when stderr is not a TTY so captured/CI output isn't spammed with
        # escape codes (tqdm achieves this with disable=None).
        self._stream = sys.stderr
        if hasattr(self._stream, "original_stream"):
            self._stream = self._stream.original_stream

        try:
            disable = not self._stream.isatty()
        except Exception:  # Catch all the things, pylint: disable=broad-except
            # Fail closed: if TTY capability cannot be determined, disable the
            # bar rather than risk spamming a non-interactive log/CI with
            # escape codes.
            disable = True

        # Fixed-layout columns so the bar never moves: a constant description,
        # then the bar, then percentage/count/unit, and finally the current
        # item via a callback column at the very end (the only part that
        # changes width). Mirrors tqdm's "{desc}|{bar}| n/total unit postfix".
        from barflow import (  # pylint: disable=I0021,import-error
            columns as _bfcols,
        )

        # Match Nuitka's tqdm/rich styling: bold-blue description + postfix
        # (info style), bold-green percentage. barflow.style speaks the same
        # "bold blue" grammar, so reuse the module-level style tuples.
        info_style = " ".join(_progress_info_style)
        pct_style = " ".join(_progress_percentage_style)
        unit_label = (" " + unit + "s") if unit else ""

        columns = [
            _bfcols.DescriptionColumn(style=info_style),
            _bfcols.TextColumn(" "),
            _bfcols.BarColumn(width=25),
            _bfcols.TextColumn(" "),
            _bfcols.PercentColumn(style=pct_style),
            _bfcols.TextColumn(" "),
            _bfcols.CountColumn(),
            _bfcols.TextColumn(unit_label),
            _bfcols.CallbackColumn(lambda task: self._postfix, style=info_style),
        ]

        self.barflow_progress = _barflow.Progress(
            *columns,
            total=effective_total,
            desc=stage,
            disable=disable
        )
        self.barflow_progress.__enter__()

    @staticmethod
    def _effectiveTotal(total, min_total):
        if total is not None:
            if min_total is not None:
                return max(total, min_total)
            return max(total, 0)
        if min_total is not None and min_total > 0:
            return min_total
        return None

    def __iter__(self):
        for val in self.iterable:
            yield val
            self.update()

    def updateTotal(self, total):
        if total != self.total:
            self.total = total
            self.barflow_progress.set_total(
                0, self._effectiveTotal(total, self.min_total)
            )

    def setCurrent(self, item):
        # Update only the trailing postfix (rendered by the callback column),
        # leaving the description fixed so the bar stays anchored.
        if item != self.item:
            self.item = item
            self._postfix = (" - %s" % item) if item is not None else ""

    def update(self):
        self.barflow_progress.advance(1)

    def _eraseLine(self):
        # barflow's close() only stops the render thread; it does not clear
        # the bar line. Emit the same erase tqdm's leave=False would, so the
        # residual bar doesn't get appended to by later output.
        try:
            if self._stream.isatty():
                self._stream.write("\r\x1b[2K")
                self._stream.flush()
        except Exception:  # Catch all the things, pylint: disable=broad-except
            pass

    def clear(self):
        self._eraseLine()

    def close(self):
        with withNoExceptions():
            self.barflow_progress.close()
        self._eraseLine()

    @contextmanager
    def withExternalWritingPause(self):
        # barflow's pause() both suspends the render thread AND erases the bar
        # area (via the same walk-back write_above uses), so the external
        # writer owns a clean screen; resume() repaints the bar below. This is
        # the parity-critical path: without a true suspend, barflow's
        # autonomous render thread would repaint mid-write and tear the output,
        # unlike tqdm/rich which only paint synchronously. No separate
        # _eraseLine() is needed — pause() already clears.
        self.barflow_progress.pause()
        try:
            yield
        finally:
            with withNoExceptions():
                self.barflow_progress.resume()


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
_rich_console = None


def _getRichModule():
    """Get the rich module if possible, might return None."""
    # Singleton, pylint: disable=global-statement
    global _rich_progress, _rich_console

    if _rich_progress:
        return _rich_progress
    elif _rich_progress is False:
        return None

    if _rich_progress is None:
        try:
            # Try importing from pip's vendored packages first
            import pip._vendor.rich.console as vendored_rich_console
            import pip._vendor.rich.progress as vendored_rich_progress

            _rich_progress = vendored_rich_progress
            _rich_console = vendored_rich_console
        except ImportError:
            try:
                import rich.console as standard_rich_console
                import rich.progress as standard_rich_progress

                _rich_progress = standard_rich_progress
                _rich_console = standard_rich_console
            except ImportError:
                _rich_progress = False

        if _rich_progress:
            if not hasattr(_rich_progress, "Progress"):
                _rich_progress = False

    if _rich_progress is False:
        return None
    else:
        atexit.register(_cleanupRich)

        return _rich_progress


def _getBarflowModule():
    """Get the barflow module if possible, might return None."""
    global _barflow  # singleton, pylint: disable=global-statement

    if _barflow:
        return _barflow
    elif _barflow is False:
        return None

    try:
        import barflow as barflow_installed  # pylint: disable=I0021,import-error

        # Validate it is really barflow with the API we use, like
        # _getRichModule() checks for Progress — a wrong/partial module named
        # "barflow" should fall back cleanly rather than crash at a call site.
        if not hasattr(barflow_installed, "Progress"):
            _barflow = False
            return None

        # pause()/resume() and the callback-column threading fix landed in
        # 0.3.1; older releases would tear or deadlock under threaded use, so
        # treat them as unavailable and fall back to tqdm/rich.
        version = tuple(
            int(part) for part in barflow_installed.__version__.split(".")[:3]
        )
        if version < (0, 3, 1):
            _barflow = False
            return None

        _barflow = barflow_installed
    except (ImportError, AttributeError, ValueError):
        _barflow = False
        return None

    return _barflow


def _checkBarflowModule():
    if _getBarflowModule() is not None:
        return "barflow"
    else:
        return "none"


def _checkRichModule():
    if _getRichModule() is not None:
        return "rich"
    else:
        return "none"


def _checkTqdmModule():
    global _colorama  # singleton, pylint: disable=global-statement

    old_colorama = sys.modules.get("colorama")

    # Prevent tqdm from seeing any system installed or previously loaded
    # colorama which it unconditionally initializes on load, wrapping Nuitka's
    # redirector and breaking Windows CRT handle inheritance. We initialize
    # colorama manually down below instead.
    sys.modules["colorama"] = None

    tqdm_module = _getTqdmModule()

    if old_colorama is not None:
        sys.modules["colorama"] = old_colorama
    else:
        del sys.modules["colorama"]

    if tqdm_module is None:
        return "none"

    if isWin32Windows():
        if _colorama is None:
            _colorama = importFromInlineCopy(
                "colorama", must_exist=True, delete_module=True
            )

        # Check for our redirection, and temporarily disable it, so colorama
        # finds the real handles.
        if hasattr(sys.stdout, "original_stream"):
            stdout_redirector = sys.stdout
            sys.stdout = stdout_redirector.original_stream
        else:
            stdout_redirector = None

        if hasattr(sys.stderr, "original_stream"):
            stderr_redirector = sys.stderr
            sys.stderr = stderr_redirector.original_stream
        else:
            stderr_redirector = None

        _colorama.init(strip=False)

        if stdout_redirector:
            stdout_redirector.original_stream = sys.stdout
            sys.stdout = stdout_redirector

        if stderr_redirector:
            stderr_redirector.original_stream = sys.stderr
            sys.stderr = stderr_redirector

    return "tqdm"


# Try progress bars in this order. barflow is preferred when installed: it
# is a C++-cored drop-in that is faster than tqdm/rich on the hot path.
_default_progress_bars = ("barflow", "tqdm", "rich")


def enableProgressBar(progress_bar):
    global use_progress_bar  # singleton, pylint: disable=global-statement

    if use_progress_bar is None:
        use_progress_bar = "none"

        if progress_bar == "auto":
            check_progress_bars = _default_progress_bars
        elif progress_bar in _default_progress_bars:
            check_progress_bars = (progress_bar,)
        else:
            check_progress_bars = ()

        for progress_bar_check in check_progress_bars:
            if progress_bar_check == "barflow":
                use_progress_bar = _checkBarflowModule()
            elif progress_bar_check == "rich":
                use_progress_bar = _checkRichModule()
            elif progress_bar_check == "tqdm":
                use_progress_bar = _checkTqdmModule()
            else:
                assert False, progress_bar_check

            if use_progress_bar != "none":
                break


def _cleanupRich():
    if use_progress_bar == "rich" and Tracing.progress is not None:
        with withNoExceptions():
            Tracing.progress.close()


def setupProgressBar(stage, unit, total, min_total=0):
    # Make sure the other was closed.
    assert Tracing.progress is None

    if use_progress_bar == "barflow":
        Tracing.progress = NuitkaProgressBarBarflow(
            iterable=None,
            stage=stage,
            total=total,
            min_total=min_total,
            unit=unit,
        )
    elif use_progress_bar == "rich":
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

        if sys.stdout.isatty():
            Tracing.my_print(Tracing.getDisableStylesCode(), end="")

        return result


def wrapWithProgressBar(iterable, stage, unit):
    if use_progress_bar == "barflow":
        result = NuitkaProgressBarBarflow(
            iterable=iterable, unit=unit, stage=stage, total=None, min_total=None
        )
        Tracing.progress = result
        return result
    elif use_progress_bar == "rich":
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
    # Three backend branches (barflow/rich/tqdm), pylint: disable=too-many-locals
    if use_progress_bar in (None, "none"):
        yield None
        return

    # Check if stdout is a TTY for Rich
    is_tty = sys.stdout.isatty()

    if use_progress_bar == "barflow":
        description = kwargs.get("desc", "Downloading")
        total_size_bytes = kwargs.get("total", 0)

        # barflow renders to stderr, so base disable on stderr's TTY status
        # (unwrapping our redirector), not the stdout-derived is_tty used by
        # the rich branch.
        bf_stream = sys.stderr
        if hasattr(bf_stream, "original_stream"):
            bf_stream = bf_stream.original_stream
        try:
            bf_disable = not bf_stream.isatty()
        except Exception:  # Catch all the things, pylint: disable=broad-except
            bf_disable = True

        barflow_progress = _barflow.Progress(
            total=total_size_bytes or None,
            desc=description,
            disable=bf_disable,
        )
        barflow_progress.__enter__()

        seen = {"n": 0}

        def onProgressBarflow(block_num=1, block_size=1, total_size=None):
            if total_size is not None and total_size > 0:
                barflow_progress.set_total(0, total_size)

            current = block_num * block_size
            delta = current - seen["n"]
            if delta > 0:
                barflow_progress.advance(delta)
                seen["n"] = current

        try:
            yield onProgressBarflow
        finally:
            with withNoExceptions():
                barflow_progress.close()
    elif use_progress_bar == "rich":
        description = kwargs.get("desc", "Downloading")
        total_size_bytes = kwargs.get("total", 0)

        # Unwrap our own redirection if we are active during SCons or similar.
        rich_file = sys.stdout
        if hasattr(rich_file, "original_stream"):
            rich_file = rich_file.original_stream

        console = _rich_console.Console(file=rich_file)

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
            console=console,
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
                    self.total = tsize  # false alarm, pylint: disable=I0021,attribute-defined-outside-init
                self.update(b * bsize - self.n)

        tqdm_kwargs = kwargs.copy()
        tqdm_kwargs.update(
            disable=None,
            leave=False,
            dynamic_ncols=True,
            bar_format="{desc} {percentage:3.1f}%|{bar:25}| {n_fmt}/{total_fmt}{postfix}"
            + getDisableStylesCode(),
        )
        with NuitkaDownloadProgressBarTqdm(*args, **tqdm_kwargs) as pb_tqdm:
            yield pb_tqdm.onProgress


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        https://www.gnu.org/licenses/agpl-3.0.txt
#
#     See also: "Nuitka Runtime Library Exception, Version 1.0" in file
#     "LICENSE-RUNTIME.txt" for additional permissions granted under Section 7.
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
