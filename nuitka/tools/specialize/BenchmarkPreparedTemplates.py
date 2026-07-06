#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Benchmark prepared code templates against legacy '%' formatting."""

import sys
import time

from nuitka.code_generation.Emission import SourceCodeCollector
from nuitka.code_generation.Indentation import indented
from nuitka.code_generation.templates.TemplateDebugWrapper import emitTemplate

from .CheckPreparedTemplates import iterPreparedTemplateChecks


def _emitUnused(_value):
    pass


def _parseIterations():
    for arg in sys.argv[1:]:
        if arg.startswith("--iterations="):
            return int(arg.split("=", 1)[1])

    return 2000


def _benchmarkLegacy(templates, iterations):
    collector = SourceCodeCollector()
    start_time = time.time()

    for _i in range(iterations):
        for _template_key, template, values in templates:
            collector(str(template) % values)

        collector.reset()

    return time.time() - start_time


def _benchmarkLegacyCollectorJoin(templates, iterations):
    collector = SourceCodeCollector()
    start_time = time.time()

    for _i in range(iterations):
        for _template_key, template, values in templates:
            collector(str(template) % values)

        _emitUnused(indented(collector))
        collector.reset()

    return time.time() - start_time


def _benchmarkPrepared(templates, iterations):
    start_time = time.time()

    for _i in range(iterations):
        for _template_key, template, values in templates:
            template.emit(_emitUnused, values)

    return time.time() - start_time


def _benchmarkPreparedCollector(templates, iterations):
    collector = SourceCodeCollector()
    start_time = time.time()

    for _i in range(iterations):
        for _template_key, template, values in templates:
            emitTemplate(template, collector, values)

        collector.reset()

    return time.time() - start_time


def _benchmarkPreparedCollectorJoin(templates, iterations):
    collector = SourceCodeCollector()
    start_time = time.time()

    for _i in range(iterations):
        for _template_key, template, values in templates:
            emitTemplate(template, collector, values)

        _emitUnused(indented(collector))
        collector.reset()

    return time.time() - start_time


def main():
    iterations = _parseIterations()
    templates = tuple(iterPreparedTemplateChecks())

    legacy_time = _benchmarkLegacy(templates, iterations)
    legacy_collector_join_time = _benchmarkLegacyCollectorJoin(templates, iterations)
    prepared_time = _benchmarkPrepared(templates, iterations)
    prepared_collector_time = _benchmarkPreparedCollector(templates, iterations)
    prepared_collector_join_time = _benchmarkPreparedCollectorJoin(
        templates, iterations
    )

    if prepared_time:
        speedup = legacy_time / prepared_time
    else:
        speedup = 0

    if prepared_collector_time:
        collector_speedup = legacy_time / prepared_collector_time
    else:
        collector_speedup = 0

    if prepared_collector_join_time:
        collector_join_speedup = (
            legacy_collector_join_time / prepared_collector_join_time
        )
    else:
        collector_join_speedup = 0

    sys.stdout.write("Prepared template benchmark:\n")
    sys.stdout.write("  Templates: %d\n" % len(templates))
    sys.stdout.write("  Iterations: %d\n" % iterations)
    sys.stdout.write("  Legacy format+emit: %.3fs\n" % legacy_time)
    sys.stdout.write("  Legacy format+emit+join: %.3fs\n" % legacy_collector_join_time)
    sys.stdout.write("  Prepared raw emit: %.3fs\n" % prepared_time)
    sys.stdout.write("  Prepared collector emit: %.3fs\n" % prepared_collector_time)
    sys.stdout.write(
        "  Prepared collector emit+join: %.3fs\n" % prepared_collector_join_time
    )
    sys.stdout.write("  Raw emit speedup: %.2fx\n" % speedup)
    sys.stdout.write("  Collector emit speedup: %.2fx\n" % collector_speedup)
    sys.stdout.write("  Collector emit+join speedup: %.2fx\n" % collector_join_speedup)


if __name__ == "__main__":
    main()


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
