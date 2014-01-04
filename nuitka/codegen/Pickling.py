#     Copyright 2014, Kay Hayen, mailto:kay.hayen@gmail.com
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
""" Module to hide the complexity of using pickle.

It should be simple, but it is not yet. Not all the pickle modules are well behaved.
"""

from nuitka import Constants, Utils

# pylint: disable=W0622
from ..__past__ import unicode
# pylint: enable=W0622

# Work around for CPython 3.x removal of cpickle.
try:
    import cPickle as cpickle
except ImportError:
    # False alarm, no double import at all, pylint: disable=W0404
    import pickle as cpickle

import pickletools

from logging import warning

if Utils.python_version >= 300:
    # Python3: The protocol 3 adds support for bytes type.
    # instead.
    pickle_protocol = 3
else:
    pickle_protocol = 2


def getStreamedConstant(constant_value):
    # Note: The marshal module cannot persist all unicode strings and
    # therefore cannot be used. Instead we use pickle.
    try:
        saved = cpickle.dumps(
            constant_value,
            protocol = 0 if type( constant_value ) is unicode else pickle_protocol
        )
    except TypeError:
        warning( "Problem with persisting constant '%r'." % constant_value )
        raise

    saved = pickletools.optimize( saved )

    # Check that the constant is restored correctly.
    try:
        restored = cpickle.loads(
            saved
        )
    except:
        warning( "Problem with persisting constant '%r'." % constant_value )
        raise

    if not Constants.compareConstants( restored, constant_value ):
        raise AssertionError(
            "Streaming of constant changed value",
            constant_value,
            "!=",
            restored,
            "types:",
            type( constant_value ),
            type( restored )
        )

    return saved
