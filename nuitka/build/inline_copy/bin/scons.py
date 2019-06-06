#!/usr/bin/env python

if __name__ == "__main__":
    import os, sys

    if sys.version_info >= (3,0) and sys.version_info < (3,5):
        sys.exit("Error, scons must not be run with Python3 older than 3.5.")

    sys.path.insert(
        0,
        os.path.normpath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "lib",
                "scons-2.3.2"
                  if sys.version_info < (2,7) else
                "scons-3.0.4"
            )
        )
    )

    # On Windows this Scons variable must be set by us.
    os.environ["SCONS_LIB_DIR"] = sys.path[0]

    import SCons.Script  # @UnresolvedImport

    # this does all the work, and calls sys.exit
    # with the proper exit status when done.
    SCons.Script.main()
