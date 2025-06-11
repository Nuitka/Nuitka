#     Copyright 2025, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


""" Display the Distributions installed. """

from nuitka.containers.OrderedSets import OrderedSet
from nuitka.Tracing import my_print
from nuitka.utils.Distributions import (
    getDistributionInstallerName,
    getDistributionName,
    getDistributions,
    getDistributionVersion,
)


def displayDistributions():
    output = OrderedSet()

    for distributions in getDistributions().values():
        for distribution in distributions:
            distribution_name = getDistributionName(distribution)

            output.add(
                (
                    distribution_name,
                    getDistributionVersion(distribution),
                    getDistributionInstallerName(distribution_name=distribution_name),
                )
            )

    for item in sorted(output):
        my_print(*item)


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
