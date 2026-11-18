#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Minimal PEP 508 requirement parsing and PEP 440 version handling.

This is used for checking project requirements when neither 'packaging' nor
'pip' is installed, e.g. in a 'uv venv'. It implements only the subset needed
for that check, not the full 'packaging' API.
"""

import os
import platform
import re
import sys

from nuitka.__past__ import long

_name_regex = re.compile(r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)")
_extras_regex = re.compile(r"\s*\[([^\]]*)\]")
_url_marker_regex = re.compile(r"^(\S+)(?:\s+;\s*(.*))?$")

_version_regex = re.compile(
    r"^\s*v?(?:(\d+)!)?"
    r"(\d+(?:\.\d+)*)"
    r"(?:[-_.]?(a|b|c|rc|alpha|beta|pre|preview)[-_.]?(\d*))?"
    r"(?:(?:-(\d+))|(?:[-_.]?(post|rev|r)[-_.]?(\d*)))?"
    r"(?:[-_.]?(dev)[-_.]?(\d*))?"
    r"(?:\+([a-z0-9]+(?:[-_.][a-z0-9]+)*))?"
    r"\s*$",
    re.IGNORECASE,
)

_specifier_regex = re.compile(r"^\s*(===|~=|==|!=|<=|>=|<|>)\s*(\S+)\s*$")

_marker_token_regex = re.compile(
    r"\s*(?:"
    r"(?P<lparen>\()|"
    r"(?P<rparen>\))|"
    r"(?P<string>'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")|"
    r"(?P<operator>===|~=|==|!=|<=|>=|<|>)|"
    r"(?P<word>[A-Za-z_][A-Za-z0-9_.]*)"
    r")"
)


class InvalidRequirement(ValueError):
    """An invalid requirement was found."""


class InvalidMarker(ValueError):
    """An invalid environment marker was found."""


class InvalidSpecifier(ValueError):
    """An invalid version specifier was found."""


class InvalidVersion(ValueError):
    """An invalid version was found."""


def _parseLetterVersion(letter, number):
    if letter:
        if not number:
            number = 0

        letter = letter.lower()

        if letter == "alpha":
            letter = "a"
        elif letter == "beta":
            letter = "b"
        elif letter in ("c", "pre", "preview"):
            letter = "rc"
        elif letter in ("rev", "r"):
            letter = "post"

        return letter, int(number)

    if number:
        return "post", int(number)

    return None


def _parseLocalVersion(local):
    if local is None:
        return None

    return tuple(
        part.lower() if not part.isdigit() else int(part)
        for part in re.split(r"[._-]", local)
    )


class Version(object):  # pylint: disable=too-many-instance-attributes
    """PEP 440 version with comparisons."""

    def __init__(self, version):
        match = _version_regex.match(version)

        if match is None:
            raise InvalidVersion("Invalid version: %r" % version)

        self.epoch = int(match.group(1) or 0)
        self.release = tuple(int(part) for part in match.group(2).split("."))
        self.pre = _parseLetterVersion(match.group(3), match.group(4))
        self.post = _parseLetterVersion(
            match.group(6), match.group(5) or match.group(7)
        )
        self.dev = _parseLetterVersion(match.group(8), match.group(9))
        self.local = _parseLocalVersion(match.group(10))
        self.is_prerelease = self.pre is not None or self.dev is not None

        parts = []

        if self.epoch:
            parts.append("%d!" % self.epoch)

        parts.append(".".join("%d" % part for part in self.release))

        self.base_version = "".join(parts)

        if self.pre is not None:
            parts.append("%s%d" % self.pre)

        if self.post is not None:
            parts.append(".post%d" % self.post[1])

        if self.dev is not None:
            parts.append(".dev%d" % self.dev[1])

        self.public = "".join(parts)

        if self.local is not None:
            parts.append(
                "+%s"
                % ".".join(
                    "%d" % part if isinstance(part, (int, long)) else part
                    for part in self.local
                )
            )

        self._version = "".join(parts)
        self._key = self._makeKey()

    def _makeKey(self):
        # Trailing zeros do not affect version ordering, so '1.0' and '1.0.0'
        # have to compare as equal.
        release = self.release

        while release and release[-1] == 0:
            release = release[:-1]

        if self.pre is None and self.post is None and self.dev is not None:
            pre = (0,)
        elif self.pre is None:
            pre = (2,)
        else:
            pre = (1,) + self.pre

        post = (0,) if self.post is None else (1,) + self.post
        dev = (1,) if self.dev is None else (0,) + self.dev

        if self.local is None:
            local = (0,)
        else:
            local = (
                1,
                tuple(
                    (1, part) if isinstance(part, (int, long)) else (0, part)
                    for part in self.local
                ),
            )

        return self.epoch, release, pre, post, dev, local

    def __str__(self):
        return self._version

    def __hash__(self):
        return hash(self._key)

    def __eq__(self, other):
        if not isinstance(other, Version):
            return NotImplemented

        return self._key == other._key

    def __ne__(self, other):
        result = self.__eq__(other)

        if result is NotImplemented:
            return result

        return not result

    def __lt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented

        return self._key < other._key

    def __le__(self, other):
        if not isinstance(other, Version):
            return NotImplemented

        return self._key <= other._key

    def __gt__(self, other):
        if not isinstance(other, Version):
            return NotImplemented

        return self._key > other._key

    def __ge__(self, other):
        if not isinstance(other, Version):
            return NotImplemented

        return self._key >= other._key


def _comparePrefix(prospective, spec):
    if prospective.epoch != spec.epoch:
        return False

    for position, spec_value in enumerate(spec.release):
        value = (
            prospective.release[position] if position < len(prospective.release) else 0
        )

        if value != spec_value:
            return False

    return True


class Specifier(object):
    """Single PEP 440 version specifier."""

    def __init__(self, specifier):
        match = _specifier_regex.match(specifier)

        if match is None:
            raise InvalidSpecifier("Invalid specifier: %r" % specifier)

        self.operator = match.group(1)
        self.version_text = match.group(2)
        self.wildcard = False
        self.version = None

        if self.operator == "===":
            return

        if self.operator in ("==", "!=") and self.version_text.endswith(".*"):
            self.wildcard = True
            version_text = self.version_text[:-2]
        else:
            version_text = self.version_text

        self.version = Version(version_text)

        if self.wildcard and (
            self.version.pre is not None
            or self.version.post is not None
            or self.version.dev is not None
            or self.version.local is not None
        ):
            raise InvalidSpecifier("Invalid specifier: %r" % specifier)

        if self.operator == "~=" and len(self.version.release) < 2:
            raise InvalidSpecifier("Invalid specifier: %r" % specifier)

    def __str__(self):
        return self.operator + self.version_text

    def _compareEqual(self, prospective):
        if self.version.local is None:
            prospective = Version(prospective.public)

        return prospective == self.version

    def _compareCompatible(self, prospective):
        # '~=2.2' is equivalent to '>=2.2,==2.*'.
        prefix = "%d!" % self.version.epoch if self.version.epoch else ""
        prefix += ".".join("%d" % part for part in self.version.release[:-1])

        return Version(prospective.public) >= self.version and _comparePrefix(
            prospective, Version(prefix)
        )

    # Many operators to support, pylint: disable=too-many-branches,too-many-return-statements,unused-argument
    def contains(self, version, prereleases):
        if self.operator == "===":
            return str(version).lower() == self.version_text.lower()

        if isinstance(version, Version):
            prospective = version
        else:
            try:
                prospective = Version(version)
            except InvalidVersion:
                return False

        if self.operator == "==":
            if self.wildcard:
                return _comparePrefix(prospective, self.version)

            return self._compareEqual(prospective)

        if self.operator == "!=":
            if self.wildcard:
                return not _comparePrefix(prospective, self.version)

            return not self._compareEqual(prospective)

        if self.operator == "~=":
            return self._compareCompatible(prospective)

        if self.operator == "<=":
            return Version(prospective.public) <= self.version

        if self.operator == ">=":
            return Version(prospective.public) >= self.version

        if self.operator == "<":
            if Version(prospective.public) >= self.version:
                return False

            # Pre-releases of the specified version are not included.
            if (
                not self.version.is_prerelease
                and prospective.is_prerelease
                and Version(prospective.base_version)
                == Version(self.version.base_version)
            ):
                return False

            return True

        if self.operator == ">":
            if Version(prospective.public) <= self.version:
                return False

            # Post-releases and local versions of the specified version are
            # not included.
            if (
                not self.version.post
                and prospective.post
                and Version(prospective.base_version)
                == Version(self.version.base_version)
            ):
                return False

            if prospective.local is not None and Version(
                prospective.base_version
            ) == Version(self.version.base_version):
                return False

            return True

        assert False, self.operator


class SpecifierSet(object):
    """Set of PEP 440 version specifiers."""

    def __init__(self, specifiers):
        self._specifiers = tuple(
            Specifier(specifier)
            for specifier in (part.strip() for part in specifiers.split(","))
            if specifier
        )

    def __str__(self):
        return ",".join(str(specifier) for specifier in self._specifiers)

    def __nonzero__(self):
        return bool(self._specifiers)

    __bool__ = __nonzero__

    def contains(self, version, prereleases):
        for specifier in self._specifiers:
            if not specifier.contains(version, prereleases=prereleases):
                return False

        return True


def _unquoteMarkerString(value):
    value = value[1:-1]

    return value.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")


def _tokenizeMarker(marker):
    tokens = []
    position = 0

    while position < len(marker):
        match = _marker_token_regex.match(marker, position)

        if match is None:
            if marker[position:].strip() == "":
                break

            raise InvalidMarker("Invalid marker: %r" % marker)

        position = match.end()
        kind = match.lastgroup
        value = match.group(kind)

        if kind == "string":
            tokens.append(("string", _unquoteMarkerString(value)))
        else:
            tokens.append((kind, value))

    return tokens


class _MarkerParser(object):
    """Recursive descent parser for PEP 508 environment markers."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def _peek(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]

        return None

    def _next(self):
        token = self._peek()

        if token is None:
            raise InvalidMarker("Unexpected end of marker")

        self.position += 1

        return token

    def _expect(self, kind):
        token = self._next()

        if token[0] != kind:
            raise InvalidMarker("Unexpected marker token %r" % (token,))

        return token

    def parse(self):
        result = self._parseOr()

        if self.position != len(self.tokens):
            raise InvalidMarker("Unexpected marker token %r" % (self._peek(),))

        return result

    def _parseOr(self):
        result = self._parseAnd()

        while self._peek() == ("word", "or"):
            self._next()
            result = ("or", result, self._parseAnd())

        return result

    def _parseAnd(self):
        result = self._parseItem()

        while self._peek() == ("word", "and"):
            self._next()
            result = ("and", result, self._parseItem())

        return result

    def _parseItem(self):
        if self._peek() == ("lparen", "("):
            self._next()
            result = self._parseOr()
            self._expect("rparen")

            return result

        lhs = self._parseValue()
        operator = self._parseOperator()
        rhs = self._parseValue()

        return "comparison", lhs, operator, rhs

    def _parseValue(self):
        token = self._next()

        if token[0] == "string":
            return "string", token[1]

        if token[0] == "word" and token[1] not in ("and", "or", "in", "not"):
            return "variable", token[1]

        raise InvalidMarker("Unexpected marker value %r" % (token,))

    def _parseOperator(self):
        token = self._next()

        if token[0] == "operator":
            return token[1]

        if token == ("word", "in"):
            return "in"

        if token == ("word", "not"):
            token = self._expect("word")

            if token[1] != "in":
                raise InvalidMarker("Expected 'not in' marker operator")

            return "not in"

        raise InvalidMarker("Expected marker operator, got %r" % (token,))


def _getMarkerEnvironment():
    if hasattr(sys, "implementation"):
        implementation_version = "%d.%d.%d" % (
            sys.implementation.version[0],
            sys.implementation.version[1],
            sys.implementation.version[2],
        )
        implementation_name = sys.implementation.name
    else:
        implementation_version = "0"
        implementation_name = ""

    return {
        "extra": "",
        "implementation_name": implementation_name,
        "implementation_version": implementation_version,
        "os_name": os.name,
        "platform_machine": platform.machine(),
        "platform_python_implementation": platform.python_implementation(),
        "platform_release": platform.release(),
        "platform_system": platform.system(),
        "platform_version": platform.version(),
        "python_full_version": platform.python_version(),
        "python_version": ".".join(platform.python_version_tuple()[:2]),
        "sys_platform": sys.platform,
    }


def _resolveMarkerValue(value, environment):
    if value[0] == "string":
        return value[1]

    try:
        return environment[value[1]]
    except KeyError:
        raise InvalidMarker("%r is not a valid marker variable" % value[1])


def _evaluateMarkerComparison(lhs, operator, rhs):
    # Many operators to support, pylint: disable=too-many-return-statements
    if operator == "in":
        return lhs in rhs

    if operator == "not in":
        return lhs not in rhs

    try:
        specifier = Specifier(operator + rhs)
    except (InvalidSpecifier, InvalidVersion):
        specifier = None

    if specifier is not None:
        try:
            return specifier.contains(lhs, prereleases=True)
        except InvalidVersion:
            pass

    if operator == "==":
        return lhs == rhs
    elif operator == "!=":
        return lhs != rhs
    elif operator == "<":
        return lhs < rhs
    elif operator == "<=":
        return lhs <= rhs
    elif operator == ">":
        return lhs > rhs
    elif operator == ">=":
        return lhs >= rhs
    elif operator == "===":
        return lhs.lower() == rhs.lower()

    raise InvalidMarker("Unsupported marker operator %r" % operator)


def _evaluateMarker(node, environment):
    kind = node[0]

    if kind == "or":
        return _evaluateMarker(node[1], environment) or _evaluateMarker(
            node[2], environment
        )

    if kind == "and":
        return _evaluateMarker(node[1], environment) and _evaluateMarker(
            node[2], environment
        )

    assert kind == "comparison", kind

    return _evaluateMarkerComparison(
        lhs=_resolveMarkerValue(node[1], environment),
        operator=node[2],
        rhs=_resolveMarkerValue(node[3], environment),
    )


class Marker(object):
    """PEP 508 environment marker."""

    def __init__(self, marker):
        self._marker = marker
        self._node = _MarkerParser(_tokenizeMarker(marker)).parse()

    def __str__(self):
        return self._marker

    def evaluate(self):
        return _evaluateMarker(self._node, _getMarkerEnvironment())


class FallbackRequirement(object):
    """PEP 508 requirement."""

    # Many parts of the requirement syntax, pylint: disable=too-many-branches,too-many-statements
    def __init__(self, requirement):
        requirement = requirement.strip()

        match = _name_regex.match(requirement)

        if match is None:
            raise InvalidRequirement("Invalid requirement: %r" % requirement)

        self.name = match.group(1)
        position = match.end()

        extras_match = _extras_regex.match(requirement, position)

        if extras_match is not None:
            extras_text = extras_match.group(1).strip()

            if extras_text:
                extras = [extra.strip() for extra in extras_text.split(",")]

                for extra in extras:
                    extra_match = _name_regex.match(extra)

                    if extra_match is None or extra_match.end() != len(extra):
                        raise InvalidRequirement("Invalid requirement extra %r" % extra)

                self.extras = tuple(extras)
            else:
                self.extras = ()

            position = extras_match.end()
        else:
            self.extras = ()

        rest = requirement[position:].strip()

        if rest.startswith("@"):
            match = _url_marker_regex.match(rest[1:].strip())

            if match is None:
                raise InvalidRequirement("Invalid requirement URL: %r" % rest)

            self.url = match.group(1)
            marker = match.group(2)

            if marker is not None:
                marker = marker.strip()

                if not marker:
                    raise InvalidRequirement(
                        "Empty requirement marker: %r" % requirement
                    )

            self.specifier = SpecifierSet("")
        else:
            marker_position = rest.find(";")

            if marker_position != -1:
                specifier_text = rest[:marker_position].strip()
                marker = rest[marker_position + 1 :].strip()

                if not marker:
                    raise InvalidRequirement(
                        "Empty requirement marker: %r" % requirement
                    )
            else:
                specifier_text = rest
                marker = None

            if specifier_text.startswith("(") and specifier_text.endswith(")"):
                specifier_text = specifier_text[1:-1].strip()

            try:
                self.specifier = SpecifierSet(specifier_text)
            except (InvalidSpecifier, InvalidVersion) as e:
                raise InvalidRequirement(str(e))

            self.url = None

        if marker:
            try:
                self.marker = Marker(marker)
            except InvalidMarker as e:
                raise InvalidRequirement(str(e))
        else:
            self.marker = None

    def __str__(self):
        parts = [self.name]

        if self.extras:
            parts.append("[%s]" % ",".join(self.extras))

        if self.specifier:
            parts.append(str(self.specifier))

        if self.url:
            parts.append("@ %s" % self.url)

        if self.marker:
            parts.append("; %s" % self.marker)

        return " ".join(parts)


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
