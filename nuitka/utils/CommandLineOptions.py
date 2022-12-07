#     Copyright 2022, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Tools for command line options."""


import sys
from optparse import IndentedHelpFormatter, OptionParser


class OurOptionParser(OptionParser):
    # spell-checker: ignore rargs
    def _process_long_opt(self, rargs, values):
        arg = rargs[0]

        if "=" not in arg:
            opt = self._match_long_opt(arg)
            option = self._long_opt[opt]
            if option.takes_value():
                self.error(
                    "The '%s' option requires an argument with '%s='." % (opt, opt)
                )

        return OptionParser._process_long_opt(self, rargs, values)


class OurHelpFormatter(IndentedHelpFormatter):
    def format_option_strings(self, option):
        """Return a comma-separated list of option strings & meta variables."""

        # Need to use private option list of our parent, pylint: disable=protected-access
        if option.takes_value():
            metavar = option.metavar or option.dest.upper()
            long_opts = [
                self._long_opt_fmt % (lopt, metavar) for lopt in option._long_opts
            ]
        else:
            long_opts = option._long_opts

        if option._short_opts and not long_opts:
            sys.exit("Error, cannot have short only options with no long option name.")

        return long_opts[0]


def makeOptionsParser(usage):
    return OurOptionParser(usage=usage, formatter=OurHelpFormatter())
