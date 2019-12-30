#!/usr/bin/env python

""" This is our runner for the inline copy of scons.

It dispatches based on the Python version it is running in, with 2.6 using a
very old version. Once scons stops supporting Python2.7 as well, we might have
to add another one.

"""


if __name__ == "__main__":
    import os
    import sys

    if sys.version_info >= (3,0) and sys.version_info < (3,5):
        sys.exit("Error, scons must not be run with Python3 older than 3.5.")

    sys.path.insert(
        0,
        os.path.abspath(
            os.path.normpath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "lib",
                    "scons-2.3.2"
                    if sys.version_info < (2,7) else
                    "scons-3.1.2"
                ),
            )
        )
    )

    # On Windows this Scons variable must be set by us.
    os.environ["SCONS_LIB_DIR"] = sys.path[0]

    import SCons.Script  # pylint: disable=import-error

    # this does all the work, and calls sys.exit
    # with the proper exit status when done.
    SCons.Script.main()
