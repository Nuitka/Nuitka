Before submitting an Issue, please review the [Issue Guidelines](https://github.com/kayhayen/Nuitka/blob/master/CONTRIBUTING.md#submitting-an-issue).

* Please check whether the bug was already reported or fixed.

* Please check out if the develop version of Nuitka works better for you.

  Download source, packages [from here](http://nuitka.net/pages/download.html)
  where you will also find instructions how to do it via PyPI.

If you want to post a problem/bug, to help us understand and resolve your issue
please check that you have provided at least the information below, and discard
up to here:

*  Nuitka version, full Python version and Platform (Windows, OSX, Linux ...)

   python -m nuitka --version

*  How did you install Nuitka and Python (pip, anaconda, deb, rpm, from source,
   what is a virtualenv ...), this is very important usually.

*  Many times when you get an error from Nuitka, your setup may be so special
   that even a "hello world" program will not work, please try that and report
   it instead.

*  If possible please supply a [Short, Self Contained, Correct, Example](http://sscce.org/)
   that demonstrates the issue i.e a small piece of code which reproduces
   the issue and can be run with out any other (or as few as possible)
   external dependencies.

*  If this is a regression (used to work in an earlier version of Nuitka),
   please note what you know about that.
