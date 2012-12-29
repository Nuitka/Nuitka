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
""" Attribute registry.

Other modules can register here handlers for attribute lookups on something, so they can
be computed at run time. This is used to predict object members and can be used for more.

"""

_attribute_handlers = {}

def registerAttributeHandlers( kinds, handler ):
    assert type( kinds ) in ( tuple, list )

    for kind in kinds:
        registerAttributeHandler( kind, handler )


def registerAttributeHandler( kind, handler ):
    assert type( kind ) is str

    assert kind not in _attribute_handlers

    _attribute_handlers[ kind ] = handler


def computeAttribute( source_node, constraint_collection ):
    lookup_source = source_node.getLookupSource()

    if lookup_source.kind in _attribute_handlers:
        return _attribute_handlers[ lookup_source.kind ](
            source_node,
            lookup_source,
            constraint_collection
        )
    else:
        constraint_collection.removeKnowledge( source_node )

        return source_node, None, None
