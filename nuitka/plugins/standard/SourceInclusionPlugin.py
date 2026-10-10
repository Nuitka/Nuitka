#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Plugin for including selected source files recorded from probe execution."""

import os
import shlex
import sys

from nuitka.containers.OrderedDicts import OrderedDict
from nuitka.importing.FakeModules import makeFakeModuleDescription
from nuitka.options.Options import (
    getMainEntryPointFilenames,
    shallMakeDll,
    shallMakeModule,
)
from nuitka.plugins.PluginBase import NuitkaPluginBase
from nuitka.utils.Execution import executeProcess
from nuitka.utils.Json import loadJsonFromContents
from nuitka.utils.ModuleNames import ModuleName


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

        command = [sys.executable, "-c", probe_code, main_filename]
        command += list(probe_args)

        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf8"

        process_result = executeProcess(
            command=command,
            env=env,
            stdin=False,
            timeout=self.source_inclusion_timeout,
        )

        stdout = _decodeCommandOutput(process_result.stdout).strip()
        stderr = _decodeCommandOutput(process_result.stderr).strip()

        probe_result, probe_error = self._decodeProbeResult(
            main_filename=main_filename, stdout=stdout
        )

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

        return probe_result

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

        source_data = probe_result.get("sources", {})

        if type(source_data) is not dict:
            return self.sysexit(
                "Error, probe execution for '%s' returned invalid source data."
                % main_filename
            )

        ordered_source_data = OrderedDict()

        for key in sorted(source_data):
            ordered_source_data[key] = source_data[key]

        return ordered_source_data, probe_result.get("error")

    @staticmethod
    def _getProbeCode():
        return r"""
from __future__ import absolute_import
from __future__ import print_function

import io
import json
import linecache
import os
import runpy
import sys


def _main():
    main_filename = os.path.abspath(sys.argv[1])
    probe_args = sys.argv[2:]

    source_data = {}

    original_getlines = linecache.getlines

    def _recording_getlines(filename, module_globals=None):
        lines = original_getlines(filename, module_globals)

        if lines and module_globals is not None:
            module_name = module_globals.get("__name__")
            module_filename = module_globals.get("__file__")

            if (
                module_name is not None
                and module_filename is not None
                and os.path.normcase(os.path.abspath(module_filename))
                == os.path.normcase(os.path.abspath(filename))
            ):
                previous_lines = source_data.get(module_name)

                if previous_lines is not None and previous_lines != lines:
                    raise AssertionError(
                        "Conflicting source recorded for module '%s'." % module_name
                    )

                source_data[module_name] = lines

        return lines

    linecache.getlines = _recording_getlines

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
        % json.dumps(
            {"sources": source_data, "error": probe_error}, sort_keys=True
        )
    )

    if probe_error is not None:
        sys.exit(1)

_main()
""".strip()

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
