#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Plugins usage statistics"""

from nuitka.States import states
from nuitka.Tracing import printIndented, printLine
from nuitka.utils.Timing import TimerReport

counted_plugin_methods = {}


def counted_plugin_method(plugin_method):
    name = "Plugins." + plugin_method.__name__

    def wrapped_plugin_method(*args, **kw):
        if states.show_plugin_usage:
            if name not in counted_plugin_methods:
                counted_plugin_methods[name] = [0, 0.0]

            counted_plugin_methods[name][0] += 1

            timer_report = TimerReport(
                message="", decider=False, include_sleep_time=False
            )
            with timer_report:
                result = plugin_method(*args, **kw)

            counted_plugin_methods[name][1] += timer_report.getTimer().getDelta()

            return result

        return plugin_method(*args, **kw)

    return wrapped_plugin_method


def printPluginUsageStats():
    if not states.show_plugin_usage:
        return

    if counted_plugin_methods:
        printLine("Plugin method calls:")

        for name, (count, total_time) in sorted(
            counted_plugin_methods.items(), key=lambda x: x[1][1], reverse=True
        ):
            average_time = total_time / count if count > 0 else 0.0
            printIndented(
                1,
                "%s calls: %d, total time: %.3fs, avg time: %.5fs"
                % (name, count, total_time, average_time),
            )


#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     Licensed under the GNU Affero General Public License, Version 3 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#        http://www.gnu.org/licenses/agpl.txt
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
