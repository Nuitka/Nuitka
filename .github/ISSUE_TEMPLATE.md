Before submitting an Issue, please review the [Issue Guidelines](https://github.com/kayhayen/Nuitka/blob/master/CONTRIBUTING.md#submitting-an-issue).

* Please check whether the bug was already reported or fixed.

* Please check out if the develop version of Nuitka works better for you.

  Download source, packages [from here](https://nuitka.net/doc/download.html)
  where you will also find instructions how to do it via pip.

If you want to post a problem/bug, to help us understand and resolve your issue
please check that you have provided at least the information below, and discard
up to here:

* Nuitka version, full Python version, flavor, OS, etc. as output by this
  command (it does more than you think, and we are adding more all the time):

  > python -m nuitka --version


* How did you install Nuitka and Python

  Did you use pip, anaconda, deb, rpm, from source, git clone, then install into
  a virtualenv or not, this is very important usually.

* The specific PyPI names and versions

  It should be taken from this output if there specific packages involved, e.g.
  `numpy`, you are expected to shorten this to the relevant ones.

  > python -m pip freeze

* Many times when you get an error from Nuitka, your setup may be special

  Then even a `print("hello world")` program will not work, please try that and report
  that instead.

* Also supply a [Short, Self Contained, Correct, Example](https://sscce.org/)

  That demonstrates the issue i.e a small piece of code which reproduces
  the issue and can be run with out any other (or as few as possible)
  external dependencies. Issues without this may get rejected without much
  consideration.

* Provide in your issue the Nuitka options used

  Ideally use the project feature, so options and example code go alone

  [Nuitka Options in the code](https://nuitka.net/doc/user-manual.html#nuitka-options-in-the-code)

* Note if this is a regression

  If it used to work in an earlier version of Nuitka, please note what you know
  about that.

* Consider getting commercial support

  [Nuitka commercial](https://nuitka.net/doc/commercial.html) offers subscriptions and priority
  support. This will accelerate your problem solution and helps to sustain Nuitka development.

Some things are not welcome, please consider it.

* Do *not* post screenshots

  These are not welcome unless absolutely necessary, e.g. because of Qt display
  problem, instead capture the output of programs, so things are searchable and
  copy&paste will work. I just plainly don't want to manually copy strings and
  hope they match.

* Do *not* close the issue yourself, we will close things on stable releases

  We close issues only when they are released as a stable version, e.g. in a
  hotfix or a new release, before that it will be "Done" in planning and go
  through `factory` and `develop` tags to indicate they are solved there.

  Of course, if you find out your issue is invalid, please close it, and
  attach the `invalid` tag.

* Do *not* report against factory version

  Unless you were asked to test it there, it is frequently very broken, and
  there is only noise to be had.

* Do *not* let this template remain part of the issue, it's noise.
