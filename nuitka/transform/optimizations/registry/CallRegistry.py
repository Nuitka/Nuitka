#     Copyright 2012, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Call registry.

Other modules can register here handlers for calls to something, so they can be computed
at run time. This is used to convert builtin name references to actual builtin nodes and
can be used for more.

"""


_call_handlers = {}

def registerCallHandlers( kinds, handler ):
    assert type( kinds ) in ( tuple, list )

    for kind in kinds:
        registerCallHandler( kind, handler )


def registerCallHandler( kind, handler ):
    assert type( kind ) is str

    assert kind not in _call_handlers

    _call_handlers[ kind ] = handler


def computeCall( call_node, constraint_collection ):
    called = call_node.getCalled()

    if called.kind in _call_handlers:
        result = _call_handlers[ called.kind ]( call_node, called )

        assert len( result ) == 3, call_node
        assert result[0] is not None, called.kind

        return result
    else:
        # TODO: Arguments if mutable, should be removed too.
        constraint_collection.removeKnowledge( called )

        return call_node, None, None
