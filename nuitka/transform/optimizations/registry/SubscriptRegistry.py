#     Copyright 2012, Kay Hayen, mailto:kayhayen@gmx.de
#
#     Part of "Nuitka", an optimizing Python compiler that is compatible and
#     integrates with CPython, but also works on its own.
#
#     If you submit patches or make the software available to licensors of
#     this software in either form, you automatically them grant them a
#     license for your part of the code under "Apache License 2.0" unless you
#     choose to remove this notice.
#
#     Kay Hayen uses the right to license his code under only GPL version 3,
#     to discourage a fork of Nuitka before it is "finished". He will later
#     make a new "Nuitka" release fully under "Apache License 2.0".
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, version 3 of the License.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#     Please leave the whole of this copyright notice intact.
#
""" Subscript registry.

Other modules can register here handlers for subscript lookups on something, so they can
be computed at run time. This is used to predict list slices and dictionary elements and
can be used for more.

"""

_subscript_handlers = {}

def registerSubscriptHandlers( kinds, handler ):
    assert type( kinds ) in ( tuple, list )

    for kind in kinds:
        registerSubscriptHandler( kind, handler )


def registerSubscriptHandler( kind, handler ):
    assert type( kind ) is str

    assert kind not in _subscript_handlers

    _subscript_handlers[ kind ] = handler


def computeSubscript( source_node ):
    lookup_source = source_node.getLookupSource()

    if lookup_source.kind in _subscript_handlers:
        return _subscript_handlers[ lookup_source.kind ]( source_node, lookup_source )
    else:
        return source_node, None, None
