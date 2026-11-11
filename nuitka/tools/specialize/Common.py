#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Common helper functions for specializing code."""

from nuitka.Constants import the_empty_unicode
from nuitka.containers.Namedtuples import makeNamedtupleClass
from nuitka.options.CommandLineOptionsTools import makeOptionsParser
from nuitka.tools.quality.auto_format.AutoFormat import (
    withFileOpenedAndAutoFormatted,
)
from nuitka.tools.release.Copyright import (
    attachLeadingComment,
    getCopyrightClaim,
    getLicenseTextCommercial,
    getLicenseTextStandard,
)
from nuitka.tools.release.Release import getBranchRemoteIdentifier
from nuitka.Tracing import tools_logger
from nuitka.Version import getCommercialVersion


def getLicenseGeneratedCode():
    if getCommercialVersion() is None or getBranchRemoteIdentifier() == "internal":
        return getLicenseTextStandard()
    else:
        return getLicenseTextCommercial()


def writeLine(output, *args):
    if not args:
        output.write("\n")
    elif len(args) == 1:
        output.write(args[0] + "\n")
    else:
        assert False, args


# Python2 dict methods:
python2_dict_methods = (  # we have full coverage for all methods
    "clear",
    "copy",
    "fromkeys",
    "get",
    "has_key",
    "items",
    "iteritems",
    "iterkeys",
    "itervalues",
    "keys",
    "pop",
    "popitem",
    "setdefault",
    "update",
    "values",
    "viewitems",
    "viewkeys",
    "viewvalues",
)

python3_dict_methods = (
    # see Python2 methods, these are only less
    "clear",
    "copy",
    "fromkeys",
    "get",
    "items",
    "keys",
    "pop",
    "popitem",
    "setdefault",
    "update",
    "values",
)

python2_str_methods = (  # we have full coverage for all methods
    "capitalize",
    "center",
    "count",
    "decode",
    "encode",
    "endswith",
    "expandtabs",
    "find",
    "format",
    "index",
    "isalnum",
    "isalpha",
    "isdigit",
    "islower",
    "isspace",
    "istitle",
    "isupper",
    "join",
    "ljust",
    "lower",
    "lstrip",
    "partition",
    "replace",
    "rfind",
    "rindex",
    "rjust",
    "rpartition",
    "rsplit",
    "rstrip",
    "split",
    "splitlines",
    "startswith",
    "strip",
    "swapcase",
    "title",
    "translate",
    "upper",
    "zfill",
)

python3_str_methods = (  # we have full coverage for all methods
    "capitalize",
    "casefold",
    "center",
    "count",
    "encode",
    "endswith",
    "expandtabs",
    "find",
    "format",
    "format_map",
    "index",
    "isalnum",
    "isalpha",
    "isascii",
    "isdecimal",
    "isdigit",
    "isidentifier",
    "islower",
    "isnumeric",
    "isprintable",
    "isspace",
    "istitle",
    "isupper",
    "join",
    "ljust",
    "lower",
    "lstrip",
    "maketrans",
    "partition",
    # TODO: Python3.9 or higher:
    # "removeprefix",
    # "removesuffix",
    "replace",
    "rfind",
    "rindex",
    "rjust",
    "rpartition",
    "rsplit",
    "rstrip",
    "split",
    "splitlines",
    "startswith",
    "strip",
    "swapcase",
    "title",
    "translate",
    "upper",
    "zfill",
)

python2_unicode_methods = (
    "capitalize",
    "center",
    "count",
    "decode",
    "encode",
    "endswith",
    "expandtabs",
    "find",
    "format",
    "index",
    "isalnum",
    "isalpha",
    "isdecimal",
    "isdigit",
    "islower",
    "isnumeric",
    "isspace",
    "istitle",
    "isupper",
    "join",
    "ljust",
    "lower",
    "lstrip",
    "partition",
    "replace",
    "rfind",
    "rindex",
    "rjust",
    "rpartition",
    "rsplit",
    "rstrip",
    "split",
    "splitlines",
    "startswith",
    "strip",
    "swapcase",
    "title",
    "translate",
    "upper",
    "zfill",
)

python3_bytes_methods = (
    "capitalize",
    "center",
    "count",
    "decode",
    "endswith",
    "expandtabs",
    "find",
    # static method
    # "fromhex",
    # TODO: Python3.5 or higher:
    # "hex",
    "index",
    "isalnum",
    "isalpha",
    "isdigit",
    "islower",
    "isspace",
    "istitle",
    "isupper",
    # TODO: Python3.7 or higher:
    # "ishex",
    # "isascii",
    "join",
    "ljust",
    "lower",
    "lstrip",
    # static method
    # "maketrans",
    "partition",
    # TODO: Python3.9 or higher:
    # "removeprefix",
    # "removesuffix",
    "replace",
    "rfind",
    "rindex",
    "rjust",
    "rpartition",
    "rsplit",
    "rstrip",
    "split",
    "splitlines",
    "startswith",
    "strip",
    "swapcase",
    "title",
    "translate",
    "upper",
    "zfill",
)

python2_list_methods = (
    "append",
    "count",
    "extend",
    "index",
    "insert",
    "pop",
    "remove",
    "reverse",
    "sort",
)

python3_list_methods = (
    "append",
    "clear",
    "copy",
    "count",
    "extend",
    "index",
    "insert",
    "pop",
    "remove",
    "reverse",
    "sort",
)

python2_type_methods = (
    # TODO: Totally incomplete
)

python3_type_methods = (
    # TODO: Totally incomplete
    "__prepare__",
)


SpecVersion = makeNamedtupleClass(
    "SpecVersion",
    (
        "spec_name",
        "python_criterion",
        "python_version_spec",
        "python_condition",
        "spec",
        "suffix",
    ),
)

MethodVariations = makeNamedtupleClass(
    "MethodVariations",
    (
        "present",
        "arg_names",
        "arg_tests",
        "arg_name_mapping",
        "arg_counts",
        "result_shape",
        "spec_versions",
    ),
)


_spec_versions_cache = {}


def _getSpecVersionsDict(spec_module):
    """Get the spec versions of a module, grouped by spec name.

    Args:
        spec_module: Module with parameter specs.

    Returns:
        Dictionary of spec name to list of 'SpecVersion' values.
    """
    result = _spec_versions_cache.get(spec_module)

    if result is None:
        result = {}

        for spec_name, spec in getSpecs(spec_module):
            for version, str_version in (
                (0x300, "3"),
                (0x370, "37"),
                (0x380, "38"),
                (0x390, "39"),
                (0x3A0, "310"),
                (0x3B0, "311"),
                (0x3C0, "312"),
                (0x3D0, "313"),
                (0x3E0, "314"),
                (0x3F0, "315"),
            ):
                if spec_name.endswith("_since_%s_spec" % str_version):
                    python_criterion = ">= 0x%x" % version
                    suffix = "Since%s" % str_version
                    break

                if spec_name.endswith("_before_%s_spec" % str_version):
                    python_criterion = "< 0x%x" % version
                    suffix = "Before%s" % str_version
                    break
            else:
                python_criterion = None
                suffix = ""

            assert ".entry_points" not in spec_name or python_criterion is not None

            if spec.name not in result:
                result[spec.name] = []

            result[spec.name].append(
                SpecVersion(
                    spec_name=spec_name,
                    python_criterion=python_criterion,
                    python_version_spec=python_criterion,
                    python_condition=(
                        None
                        if python_criterion is None
                        else "python_version %s" % python_criterion
                    ),
                    spec=spec,
                    suffix=suffix,
                )
            )

        # Sort and tighten the criteria only once all versions of a spec are known.
        for spec_versions in result.values():
            spec_versions.sort(
                key=lambda spec_version: spec_version.python_criterion or "",
                reverse=True,
            )

            # Logic to tighten the criteria for older versions to not match the
            # newer versions.
            for i, spec_version in enumerate(spec_versions):
                if i > 0:
                    prev_spec_version = spec_versions[i - 1]

                    if (
                        prev_spec_version.python_criterion
                        and spec_version.python_criterion
                        and prev_spec_version.python_criterion.startswith(">= ")
                        and spec_version.python_criterion.startswith(">= ")
                    ):
                        limit = prev_spec_version.python_criterion.replace(">=", "<")
                        new_criterion = "%s and python_version %s" % (
                            spec_version.python_criterion,
                            limit,
                        )
                        new_spec = "%s, %s" % (spec_version.python_version_spec, limit)

                        spec_versions[i] = spec_version.replace(
                            python_criterion=new_criterion,
                            python_version_spec=new_spec,
                            python_condition="%s <= python_version %s"
                            % (
                                spec_version.python_criterion.replace(">= ", "", 1),
                                limit,
                            ),
                        )

        _spec_versions_cache[spec_module] = result

    return result


def getSpecVersions(spec_module):
    """Get the spec versions of a module.

    Args:
        spec_module: Module with parameter specs.

    Returns:
        Tuple of lists of 'SpecVersion' values.
    """
    return tuple(sorted(_getSpecVersionsDict(spec_module).values()))


def getMethodSpecVersions(spec_module, shape_name, method_name):
    """Get the versioned specs of a method.

    Args:
        spec_module: Module with parameter specs.
        shape_name: Name of the type shape, e.g. 'tshape_str'.
        method_name: Name of the method, e.g. 'translate'.

    Returns:
        List of 'SpecVersion' values, or None if the method is unknown.
    """
    method_spec_name = "%s.%s" % (shape_name.split("_")[-1], method_name)

    spec_versions = _getSpecVersionsDict(spec_module).get(method_spec_name)

    if spec_versions is not None:
        versioned_specs = [
            spec_version
            for spec_version in spec_versions
            if spec_version.python_criterion is not None
        ]

        # If there are version specific specs, prefer them over any unversioned
        # alias that might still be present.
        if versioned_specs:
            spec_versions = versioned_specs

    return spec_versions


def getSpecVariation(spec):
    """Get the code generation variation of a parameter spec.

    Args:
        spec: Parameter spec to get the variation of.

    Returns:
        Tuple of argument names, argument tests, argument name mapping,
        argument counts, and result shape.
    """
    if spec.isStarListSingleArg():
        required = 1

        arg_counts = tuple(range(required, required + 2))

        arg_names = (
            spec.getStarListArgumentName(),
            spec.getStarDictArgumentName(),
        )

        arg_name_mapping = {
            "list_args": spec.getStarListArgumentName(),
        }
    else:
        required = spec.getArgumentCount() - spec.getDefaultCount()

        arg_counts = tuple(range(required, spec.getArgumentCount() + 1))

        arg_names = spec.getParameterNames()
        arg_name_mapping = {}

    arg_tests = [
        (
            ""
            if arg_name
            in (spec.getStarListArgumentName(), spec.getStarDictArgumentName())
            else "is not None"
        )
        for arg_name in arg_names
    ]

    return arg_names, arg_tests, arg_name_mapping, arg_counts, spec.getTypeShape()


def _mergeSpecVariations(spec_versions):
    """Merge the variations of the specs of a method.

    Args:
        spec_versions: List of 'SpecVersion' values.

    Returns:
        Tuple of argument names, argument tests, argument name mapping,
        argument counts, and result shape.
    """
    arg_names = []
    arg_tests_dict = {}
    arg_name_mapping = {}
    arg_counts = set()
    result_shape = None

    for spec_version in spec_versions:
        (
            variant_arg_names,
            variant_arg_tests,
            variant_arg_name_mapping,
            variant_arg_counts,
            variant_result_shape,
        ) = getSpecVariation(spec_version.spec)

        for arg_name, arg_test in zip(variant_arg_names, variant_arg_tests):
            if arg_name not in arg_names:
                arg_names.append(arg_name)

            assert arg_tests_dict.get(arg_name, arg_test) == arg_test
            arg_tests_dict[arg_name] = arg_test

        for arg_name, mapped_arg_name in variant_arg_name_mapping.items():
            assert arg_name_mapping.get(arg_name, mapped_arg_name) == mapped_arg_name
            arg_name_mapping[arg_name] = mapped_arg_name

        arg_counts.update(variant_arg_counts)

        if result_shape is None:
            result_shape = variant_result_shape
        else:
            assert result_shape is variant_result_shape, (
                result_shape,
                variant_result_shape,
            )

    arg_names = tuple(arg_names)

    return (
        arg_names,
        [arg_tests_dict[arg_name] for arg_name in arg_names],
        arg_name_mapping,
        tuple(sorted(arg_counts)),
        result_shape,
    )


def getMethodVariations(spec_module, shape_name, method_name, must_exist=False):
    """Get the variations of a method for code generation.

    Args:
        spec_module: Module with parameter specs.
        shape_name: Name of the type shape, e.g. 'tshape_str'.
        method_name: Name of the method, e.g. 'translate'.
        must_exist: Whether to assert that the method spec exists.

    Returns:
        'MethodVariations' value.
    """
    spec_versions = getMethodSpecVersions(spec_module, shape_name, method_name)

    if spec_versions is None:
        if must_exist:
            assert False, "%s.%s" % (shape_name.split("_")[-1], method_name)

        return MethodVariations(
            present=False,
            arg_names=None,
            arg_tests=None,
            arg_name_mapping=None,
            arg_counts=None,
            result_shape=None,
            spec_versions=None,
        )

    (
        arg_names,
        arg_tests,
        arg_name_mapping,
        arg_counts,
        result_shape,
    ) = _mergeSpecVariations(spec_versions)

    return MethodVariations(
        present=True,
        arg_names=arg_names,
        arg_tests=arg_tests,
        arg_name_mapping=arg_name_mapping,
        arg_counts=arg_counts,
        result_shape=result_shape,
        spec_versions=spec_versions,
    )


def getSpecs(spec_module):
    for name in sorted(dir(spec_module)):
        if name.endswith("_spec"):
            yield name, getattr(spec_module, name)


def formatArgs(args, starting=True, finishing=True, quoted=False):
    result = []
    if args:
        if not starting:
            result.append(",")

        for arg in args:
            result.append('"%s"' % arg if quoted else arg)

            if arg is not args[-1] or not finishing:
                result.append(",")

    return "".join(result)


def check():
    if str is bytes:
        for method_name in python2_str_methods:
            assert hasattr("", method_name), method_name
        for method_name in python2_unicode_methods:
            assert hasattr(the_empty_unicode, method_name), method_name
        for method_name in python2_dict_methods:
            assert hasattr({}, method_name), method_name
    else:
        for method_name in python3_str_methods:
            assert hasattr("", method_name), method_name
        for method_name in python3_dict_methods:
            assert hasattr({}, method_name), method_name


check()


check_only = False


def enableCheckOnlyMode():
    # Singleton, pylint: disable=global-statement
    global check_only
    check_only = True


def isCheckOnlyMode():
    return check_only


def traceSpecialization(message):
    if not isCheckOnlyMode():
        tools_logger.info(message)


def parseOptions():
    parser = makeOptionsParser(usage=None, epilog=None)
    parser.add_option(
        "--check",
        action="store_true",
        dest="check_only",
        default=False,
        help="""Check only, do not write files. Default is %default.""",
    )
    options, _positional_args = parser.parse_args()

    if options.check_only:
        enableCheckOnlyMode()


def withFileOpenedAndAutoFormattedWithClaim(filename, claim, ignore_errors=False):
    """Context manager for opening a file, auto-formatting it, and adding a copyright claim."""

    def addCopyrightClaimComments(tmp_filename):
        if claim:
            attachLeadingComment(
                filename=tmp_filename,
                effective_filename=filename,
                comments=getCopyrightClaim(filename=filename, claim=claim),
            )

    return withFileOpenedAndAutoFormatted(
        filename=filename,
        effective_filename=filename,
        ignore_errors=ignore_errors,
        check_only=check_only,
        post_format_hook=addCopyrightClaimComments,
    )


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
