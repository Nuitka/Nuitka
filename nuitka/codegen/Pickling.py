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

python_version = Utils.getPythonVersion()

if python_version >= 300:
    # Python3: The protocol 2 outputs bytes that I don't know how to covert to "str",
    # which protocol 0 doesn't, so stay with it. TODO: Use more efficient protocol version
    # instead.

    pickle_protocol = 0
else:
    pickle_protocol = 2



def getStreamedConstant( constant_value ):
    # Note: The marshal module cannot persist all unicode strings and
    # therefore cannot be used. Instead we use pickle.
    try:
        saved = cpickle.dumps(
            constant_value,
            protocol = pickle_protocol
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

    # If we have Python3, we need to make sure, we use UTF8 or else we get into trouble.
    if str is unicode:
        saved = saved.decode( "utf_8" )

    return saved
