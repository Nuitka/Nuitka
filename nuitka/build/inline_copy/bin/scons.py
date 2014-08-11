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

    import SCons.Script

    # this does all the work, and calls sys.exit
    # with the proper exit status when done.
    SCons.Script.main()
