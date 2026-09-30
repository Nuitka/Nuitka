#     Copyright 2026, Kay Hayen, mailto:kay.hayen@gmail.com find license text at end of file


"""Operations on the tree.

This is mostly for the different kinds of visits that the node tree can have.
You can visit a scope, a tree (module), or every scope of a tree (module).

"""

import sys

# Depth at which the iterative traversal takes over, leaving headroom for the
# caller stack and the visitor calls.
_visit_depth_threshold = sys.getrecursionlimit() // 2


def _visitorIsEnterOnly(visitor):
    # Visitors without their own leave callback only need the entering nodes,
    # which can be done much faster without post-order handling.
    return getattr(type(visitor), "onLeaveNode") is getattr(
        VisitorNoopMixin, "onLeaveNode"
    )


def visitTree(tree, visitor):
    if _visitorIsEnterOnly(visitor):
        _visitTreeEnterOnly(tree, visitor)
    else:
        _visitTreeRecursive(tree, visitor, 0)


def _visitTreeEnterOnly(tree, visitor):
    # Iterative pre-order entering using an explicit stack, so that very
    # deeply nested node trees do not exceed the Python recursion limit.
    stack = [tree]

    while stack:
        node = stack.pop()
        visitor.onEnterNode(node)
        stack.extend(node.getVisitableNodes())


def _visitTreeRecursive(tree, visitor, depth):
    if depth > _visit_depth_threshold:
        _visitTreeIterative(tree, visitor)
    else:
        visitor.onEnterNode(tree)

        for visitable in tree.getVisitableNodes():
            _visitTreeRecursive(visitable, visitor, depth + 1)

        visitor.onLeaveNode(tree)


# Stack indicator for the leave call of a node, when its children are done.
_leave_indicator = object()


def _visitTreeIterative(tree, visitor):
    # Iterative pre-/post-order traversal using an explicit stack, so that very
    # deeply nested node trees do not exceed the Python recursion limit.
    stack = [tree]

    while stack:
        item = stack.pop()

        if item is _leave_indicator:
            visitor.onLeaveNode(stack.pop())
        else:
            visitor.onEnterNode(item)
            children = item.getVisitableNodes()

            if children:
                # Revisit this node for the leave call once its children are
                # done, then push the reversed children.
                stack.append(item)
                stack.append(_leave_indicator)
                stack.extend(reversed(children))
            else:
                visitor.onLeaveNode(item)


class VisitorNoopMixin(object):
    def onEnterNode(self, node):
        """Overloaded for operation before the node children were done."""

    def onLeaveNode(self, node):
        """Overloaded for operation after the node children were done."""


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
