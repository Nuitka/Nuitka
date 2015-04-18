#! /usr/bin/env python

if __name__ == "__main__":
    import os, sys

    sys.path.insert(
        0,
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "lib",
            "scons-2.3.2"
        )
    )

    if sys.version_info[0] >= 3:
        sys.exit("""\
Error, scons must be run with Python3. Our attempts at guessing to find a
Python2 version must have failed. Ideally you would install Scons, then
Nuitka would use it and not face the issue.""")

    import SCons.Script  # @UnresolvedImport

    # this does all the work, and calls sys.exit
    # with the proper exit status when done.
    SCons.Script.main()
