#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Decisions with a reason, for use as return values."""

from .Namedtuples import makeNamedtupleClass


class DecisionBase(makeNamedtupleClass("DecisionBase", ("decision", "reason"))):
    """Base class for a decision with a reason.

    Use 'decideYes()' for positive decisions, 'decideNo(reason)' for negative
    ones, and 'decideAbstain()' when there is no opinion. Testing a decision as
    a boolean returns its 'decision' value.
    """

    __slots__ = ()

    def __nonzero__(self):
        return bool(self.decision)

    __bool__ = __nonzero__

    def __repr__(self):
        return "<%s decision=%r reason=%r>" % (
            self.__class__.__name__,
            self.decision,
            self.reason,
        )

    @classmethod
    def decideYes(cls, reason=None):
        """Create a positive decision with an optional reason."""
        return cls(True, reason)

    @classmethod
    def decideNo(cls, reason):
        """Create a negative decision with a reason."""
        return cls(False, reason)

    @classmethod
    def decideAbstain(cls, reason=None):
        """Create a decision without an opinion, optionally with a reason."""
        return cls(None, reason)

    @classmethod
    def decideFrom(cls, decision):
        """Create a decision of this class from another decision.

        Args:
            decision: Another 'DecisionBase' instance.

        Returns:
            Decision of this class with the same members.
        """
        assert isinstance(decision, DecisionBase), decision

        return cls(decision.decision, decision.reason)

    def raiseExceptionUnlessPositive(self, exception_class, template, template_args):
        """Raise the given exception unless the decision is positive.

        The decision reason is added to 'template_args' as 'reason'.

        Args:
            exception_class: Exception class to raise.
            template: Message template.
            template_args: Mapping of template values.

        Raises:
            Exception: The provided exception class if the decision is not positive.
        """
        assert type(template_args) is dict, template_args

        if not self.decision:
            template_args = dict(template_args)
            template_args["reason"] = self.reason

            raise exception_class(template % template_args)

    def sysexitUnlessPositive(self, logger, message, template_args):
        """Exit with a fatal error unless the decision is positive.

        The decision reason is added to 'template_args' as 'reason'.

        Args:
            logger: Logger to use for the fatal error.
            message: Message template.
            template_args: Mapping of template values.

        Raises:
            SystemExit: If the decision is not positive.
        """
        assert type(template_args) is dict, template_args

        if not self.decision:
            template_args = dict(template_args)
            template_args["reason"] = self.reason

            return logger.sysexit(message % template_args)


def makeDecisionClass(name):
    """Create a decision class with the given name.

    Args:
        name: Name of the decision class.

    Returns:
        class: Subclass of 'DecisionBase'.
    """

    class DynamicDecision(DecisionBase):
        __slots__ = ()
        __qualname__ = name

    DynamicDecision.__name__ = name

    return DynamicDecision


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
