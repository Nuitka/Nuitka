#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Plugin for including selected source files recorded from probe execution."""

import os
import shlex
import sys

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.importing.FakeModules import makeFakeModuleDescription
from nuitka.options.Options import (
    getMainEntryPointFilenames,
    isStandaloneMode,
    shallMakeDll,
    shallMakeModule,
)
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.PythonVersions import getSystemPrefixPath
from nuitka.utils.Execution import executeProcess, getEnvironmentPathAdded
from nuitka.utils.FileOperations import (
    getFileContents,
    getNormalizedPath,
    getNormalizedPathJoin,
    putTextFileContents,
    relpath,
    resolveShellPatternToFilenames,
    withTemporaryDirectory,
)
from nuitka.utils.Json import loadJsonFromContents
from nuitka.utils.ModuleNames import ModuleName


def _getPythonIncludeDirectories(logger):
    """Return the include directories of the running interpreter.

    Args:
        logger: Logger to report errors with.

    Notes:
        These are the directories needed for C compilation against the running
        interpreter, i.e. where 'Python.h' and the 'pyconfig.h' that describes
        it are found. On Debian and Ubuntu, the latter is a wrapper that
        includes a file from a multiarch directory outside the main include
        directory, which is returned as well.

    Returns:
        Tuple of absolute directory paths, the main include directory first,
        followed by the multiarch variant when it exists.
    """
    try:
        import sysconfig
    except ImportError:
        # Python 2.6 does not provide it, and the layouts that need more than
        # the main include directory are all much newer.
        return logger.sysexit("Error, cannot detect Python include directories.")

    result = []

    paths = sysconfig.get_paths()

    for key in ("include", "platinclude"):
        include_dir = paths.get(key)

        if include_dir is not None and os.path.isdir(include_dir):
            include_dir = getNormalizedPath(os.path.abspath(include_dir))

            if include_dir not in result:
                result.append(include_dir)

    multiarch = sysconfig.get_config_var("MULTIARCH")

    if multiarch:
        for include_dir in tuple(result):
            multiarch_dir = getNormalizedPathJoin(
                os.path.dirname(include_dir),
                multiarch,
                os.path.basename(include_dir),
            )

            if os.path.isdir(multiarch_dir) and multiarch_dir not in result:
                result.append(multiarch_dir)

    if not result:
        return logger.sysexit("Error, cannot detect Python include directories.")

    return tuple(result)


def _decodeCommandOutput(value):
    if str is not bytes:
        return value.decode("utf8", "replace")
    else:
        return value


def _joinSortedKeys(value):
    return ",".join(sorted(value))


def _formatDictLiteralCode(value):
    if not value:
        return "{}"

    result = ["{"]

    for key in value:
        result.append("    %r: %r," % (key, value[key]))

    result.append("}")

    return "\n".join(result)


_probe_result_prefix = "NUITKA_SOURCE_INCLUSION_JSON:"

_probe_records_environment = "NUITKA_SOURCE_INCLUSION_RECORDS"

_probe_records_directory_prefix = "nuitka-source-inclusion-"


def _getSiteCustomizeCode():
    """Return the code of the 'sitecustomize' module used by probe executions.

    Notes:
        The probe execution itself and all child processes that are spawned
        while it runs import this module automatically, since its directory
        is prepended to 'PYTHONPATH'. It records source files the way the
        runtime support module serves them, but writes them to per-process
        files immediately, so records survive child processes being killed.
    """
    return r"""
import json
import linecache
import os

_record_directory = os.environ.get("NUITKA_SOURCE_INCLUSION_RECORDS")

if _record_directory:
    _recorded_modules = {}
    _original_getlines = linecache.getlines

    def _recording_getlines(filename, module_globals=None):
        lines = _original_getlines(filename, module_globals)

        if lines and module_globals is not None:
            module_name = module_globals.get("__name__")
            module_filename = module_globals.get("__file__")

            if (
                module_name is not None
                and module_filename is not None
                and module_name not in _recorded_modules
                and os.path.normcase(os.path.abspath(module_filename))
                == os.path.normcase(os.path.abspath(filename))
            ):
                _recorded_modules[module_name] = True

                record_filename = os.path.join(
                    _record_directory, "records-%d.jsonl" % os.getpid()
                )

                record_file = open(record_filename, "a")
                try:
                    record_file.write(json.dumps([module_name, lines]))
                    record_file.write("\n")
                finally:
                    record_file.close()

        return lines

    linecache.getlines = _recording_getlines
"""


class NuitkaPluginSourceInclusion(NuitkaPluginBase):
    plugin_name = "source-inclusion"
    plugin_desc = (
        "Record source files from probe execution and serve them via 'linecache'."
    )
    plugin_category = "feature,package-support"

    @classmethod
    def addPluginCommandLineOptions(cls, group):
        group.add_option(
            "--source-inclusion-args",
            action="append",
            dest="source_inclusion_arg_sets",
            default=[],
            help="""\
Run the program being compiled during compilation with this shell-style
argument list while recording looked up source files. Repeat for every
additional probe run, e.g. '--source-inclusion-args="subcommand --help"'.""",
        )
        group.add_option(
            "--source-inclusion-timeout",
            action="store",
            dest="source_inclusion_timeout",
            type="int",
            default=None,
            help="""\
Timeout in seconds for each probe run. Defaults to no timeout, so a probe \
run that hangs is seen rather than silently cut short.""",
        )
        group.add_option(
            "--show-source-inclusion-trace",
            action="store_true",
            dest="show_source_inclusion_trace",
            default=False,
            help="""\
Display the recorded source inclusion modules from the probe run.""",
        )

    @classmethod
    def isRelevant(cls):
        return not (shallMakeModule() or shallMakeDll())

    def _normalizeSourceInclusionArgSets(self, source_inclusion_arg_sets):
        result = []

        for source_inclusion_arg_set in source_inclusion_arg_sets:
            try:
                result.append(tuple(shlex.split(source_inclusion_arg_set)))
            except ValueError as e:
                return self.sysexit(
                    "Error, malformed value %r for '--source-inclusion-args': %s"
                    % (source_inclusion_arg_set, e)
                )

        if not result:
            result.append(())

        return tuple(result)

    def __init__(
        self,
        source_inclusion_arg_sets,
        source_inclusion_timeout,
        show_source_inclusion_trace,
    ):
        if source_inclusion_timeout is not None and source_inclusion_timeout <= 0:
            self.sysexit(
                "Error, '--source-inclusion-timeout' must be greater than zero."
            )

        self.source_inclusion_arg_sets = self._normalizeSourceInclusionArgSets(
            source_inclusion_arg_sets=source_inclusion_arg_sets
        )

        self.source_inclusion_timeout = source_inclusion_timeout
        self.show_source_inclusion_trace = show_source_inclusion_trace

        self.main_filename = None
        self.source_data = OrderedDict()
        self.python_headers_included = False

    def onCompilationStartChecks(self):
        main_filenames = getMainEntryPointFilenames()

        if len(main_filenames) != 1:
            return self.sysexit(
                "Error, '--enable-plugin=source-inclusion' does not support multiple main programs yet."
            )

        self.main_filename = main_filenames[0]

        source_data = self._runProbeExecutions(main_filename=self.main_filename)

        self.source_data = source_data

        self.info(
            "Recorded %d source file(s) from %d probe execution(s)."
            % (len(self.source_data), len(self.source_inclusion_arg_sets))
        )

        if self.show_source_inclusion_trace:
            if self.source_data:
                self.info(
                    "Recorded source inclusion modules: %s"
                    % _joinSortedKeys(self.source_data)
                )
            else:
                self.info("Recorded source inclusion modules: none")

        if not self.source_data:
            self.warning("""\
No source file lookups were recorded. Adjust \
'--source-inclusion-args' values if source inspection still fails at run \
time.""")

    def considerDataFiles(self, module):
        """Provide the Python header files for in-place C compilation.

        Notes:
            The triton backends build C extensions in place at run time, the
            driver helpers like "cuda_utils" and the per-signature launchers,
            and need "Python.h" and "pyconfig.h" of the running interpreter to
            do so. This is true for every backend, including third party ones
            found through entry points, so the "triton.backends" package is
            used as the trigger.

        Args:
            module: The module considered.

        Yields:
            IncludedDataFile objects for the header directories.
        """
        if (
            module.getFullName() == "triton.backends"
            and isStandaloneMode()
            and not self.python_headers_included
        ):
            self.python_headers_included = True

            for include_dir in _getPythonIncludeDirectories(logger=self):
                include_relpath = relpath(include_dir, getSystemPrefixPath())

                yield self.makeIncludedDataDirectory(
                    source_path=include_dir,
                    dest_path=include_relpath,
                    reason="Python header files for in-place C compilation",
                    tags="config",
                    raw=True,
                )

    def _runProbeExecutions(self, main_filename):
        merged_source_data = {}

        for probe_args in self.source_inclusion_arg_sets:
            source_data = self._runProbeExecution(
                main_filename=main_filename, probe_args=probe_args
            )

            for key, source_code in source_data.items():
                if key in merged_source_data:
                    if merged_source_data[key] != source_code:
                        return self.sysexit(
                            "Error, probe execution for '%s' with arguments %r recorded conflicting source code for %r."
                            % (main_filename, probe_args, key)
                        )
                else:
                    merged_source_data[key] = source_code

        ordered_source_data = OrderedDict()

        for key in sorted(merged_source_data):
            ordered_source_data[key] = merged_source_data[key]

        return ordered_source_data

    def _runProbeExecution(self, main_filename, probe_args):
        probe_code = self._getProbeCode()

        with withTemporaryDirectory(
            logger=self,
            prefix=_probe_records_directory_prefix,
            ignore_errors=True,
        ) as record_dir:
            putTextFileContents(
                filename=os.path.join(record_dir, "sitecustomize.py"),
                contents=_getSiteCustomizeCode(),
            )

            command = [sys.executable, "-c", probe_code, main_filename]
            command += list(probe_args)

            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf8"
            env[_probe_records_environment] = record_dir
            env["PYTHONPATH"] = getEnvironmentPathAdded(
                "PYTHONPATH", record_dir, prefix=True
            )

            process_result = executeProcess(
                command=command,
                env=env,
                stdin=False,
                timeout=self.source_inclusion_timeout,
            )

            stdout = _decodeCommandOutput(process_result.stdout).strip()
            stderr = _decodeCommandOutput(process_result.stderr).strip()

            probe_result = self._decodeProbeResult(
                main_filename=main_filename, stdout=stdout
            )

            source_data = self._getRecordedSourceData(
                main_filename=main_filename, record_dir=record_dir
            )

        probe_error = probe_result.get("error")

        if process_result.exit_code != 0 or probe_error is not None:
            return self.sysexit(
                "Error, probe execution for '%s' with arguments %r failed with exit code %d.\nReason: %s\nStderr: %s"
                % (
                    main_filename,
                    probe_args,
                    process_result.exit_code,
                    probe_error or "program exited non-zero",
                    stderr or "<empty>",
                )
            )

        return source_data

    def _getRecordedSourceData(self, main_filename, record_dir):
        source_data = OrderedDict()

        for record_filename in resolveShellPatternToFilenames(
            os.path.join(record_dir, "records-*.jsonl")
        ):
            for record_line in getFileContents(
                record_filename, mode="r", encoding="utf8"
            ).splitlines():
                if not record_line:
                    continue

                if str is not bytes:
                    record_line = record_line.encode("utf8")

                record = loadJsonFromContents(record_line)

                if type(record) not in (list, tuple) or len(record) != 2:
                    return self.sysexit(
                        "Error, probe execution for '%s' recorded invalid data in '%s'."
                        % (main_filename, record_filename)
                    )

                module_name, lines = record

                previous_lines = source_data.get(module_name)

                if previous_lines is not None:
                    if previous_lines != lines:
                        return self.sysexit(
                            "Error, probe execution for '%s' recorded conflicting source code for module '%s'."
                            % (main_filename, module_name)
                        )
                else:
                    source_data[module_name] = lines

        return source_data

    def _decodeProbeResult(self, main_filename, stdout):
        stdout_lines = [line for line in stdout.splitlines() if line.strip()]

        if not stdout_lines:
            return self.sysexit(
                "Error, probe execution for '%s' produced no JSON result."
                % main_filename
            )

        for stdout_line in reversed(stdout_lines):
            if stdout_line.startswith(_probe_result_prefix):
                probe_result_text = stdout_line[len(_probe_result_prefix) :]
                break
        else:
            return self.sysexit(
                "Error, probe execution for '%s' did not produce a tagged JSON result."
                % main_filename
            )

        if str is not bytes:
            probe_result_text = probe_result_text.encode("utf8")

        probe_result = loadJsonFromContents(probe_result_text)

        if type(probe_result) is not dict:
            return self.sysexit(
                "Error, probe execution for '%s' did not produce valid JSON: %s"
                % (main_filename, probe_result_text)
            )

        return probe_result

    @staticmethod
    def _getProbeCode():
        return r"""
from __future__ import absolute_import
from __future__ import print_function

import io
import json
import os
import runpy
import sys


def _main():
    main_filename = os.path.abspath(sys.argv[1])
    probe_args = sys.argv[2:]

    null_output = io.open(os.devnull, "w", encoding="utf8", errors="ignore")
    old_stdout = sys.stdout
    old_stderr = sys.stderr

    probe_error = None

    try:
        sys.stdout = null_output
        sys.stderr = null_output
        sys.argv = [main_filename] + probe_args

        main_directory = os.path.dirname(main_filename)
        if main_directory:
            sys.path[0] = main_directory

        try:
            runpy.run_path(main_filename, run_name="__main__")
        except SystemExit as e:
            if e.code not in (None, 0):
                probe_error = "program exited with code %r" % (e.code,)
        except KeyboardInterrupt:
            raise
        except BaseException:
            import traceback

            probe_error = traceback.format_exc()
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        null_output.close()

    print(
        "NUITKA_SOURCE_INCLUSION_JSON:%s"
        % json.dumps({"error": probe_error}, sort_keys=True)
    )

    if probe_error is not None:
        sys.exit(1)

_main()
"""

    def createFakeModuleDependency(self, module):
        if module.getFullName() == "linecache" and self.source_data:
            return (
                makeFakeModuleDescription(
                    module_name=ModuleName("_nuitka_source_inclusion"),
                    source_code=self._getSupportModuleCode(),
                    source_filename=self.main_filename,
                    reason="recorded source inclusion support",
                ),
            )

    def createPostModuleLoadCode(self, module):
        if module.getFullName() == "linecache" and self.source_data:
            return (
                """\
import linecache
import _nuitka_source_inclusion
_nuitka_source_inclusion.install(linecache)
""",
                "Install recorded source inclusion into 'linecache'.",
            )

    def _getSupportModuleCode(self):
        source_data_code = _formatDictLiteralCode(self.source_data)

        return """\
import linecache

_source_inclusion_data = %s


def install(linecache_module):
    if getattr(linecache_module, "_nuitka_source_inclusion_installed", False):
        return

    original_getlines = linecache_module.getlines

    def nuitka_getlines(filename, module_globals=None):
        if module_globals is not None:
            module_name = module_globals.get("__name__")

            if module_name is not None:
                lines = _source_inclusion_data.get(module_name)

                if lines is not None:
                    linecache_module.cache[filename] = (None, None, lines, filename)

                    return lines

        return original_getlines(filename, module_globals)

    linecache_module.getlines = nuitka_getlines
    linecache_module._nuitka_source_inclusion_installed = True
    linecache_module._nuitka_source_inclusion_sources = _source_inclusion_data
""" % source_data_code

    def getReportData(self, make_report_path):
        yield "recorded_source_modules", _joinSortedKeys(self.source_data)


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
