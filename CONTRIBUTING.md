# Contributing to Nuitka

This document aims to give an overview of how to contribute to Nuitka. It tries
to answer commonly asked questions regarding that, and to provide some insight

* If you plan on submitting an issue, please follow this
  [template](https://github.com/kayhayen/Nuitka/blob/master/.github/ISSUE_TEMPLATE.md).
* If you want to open a pull request make sure to read the information on this
  page but also have a look at our
  [pull request template](https://github.com/kayhayen/Nuitka/blob/master/.github/PULL_REQUEST_TEMPLATE.md).

## Getting Started

* Read the [Nuitka User Manual](http://nuitka.net/doc/user-manual.html)
* Read the [Nuitka Developer Manual](http://nuitka.net/doc/developer-manual.html)
* Checkout the git repo of Nuitka

## Submitting a Pull Request

Pull requests are great. Here's a quick guide:

1. Fork the repo on github.
2. Install the `pre-commit` git hook that is going to automatically format your
   code as described in the Developer Manual.
3. Make a new branch and base your new branch on `develop`.
4. Ideally add a test specific for your change to demonstrate it. Due to Nuitka
   testing being basically to compile the whole world, it's ok to not have one.
   But obviously if you fix something, it wasn't observed by that, it would be
   good to provide a reproducer.
5. Make the tests pass.
6. Push to your fork and submit a pull request against `nuitka:develop`
7. Wait for review, suggestions for improvements or alternative ideas may
   happen. Keep in mind that PR checklist items can be met after the pull
   request has been opened by adding more commits to the branch.

All the submitted pieces including potential data must be compatible with the
Apache License 2, which already says that once you are sending source, e.g.
via pull request, you automatically license it as that too.

## Submitting an Issue

If you want to ask a question about a specific Nuitka aspect, please be kind
and first of all..

* Search through [Github issues tagged as
"question"](https://github.com/kayhayen/Nuitka/issues?q=label%3Aquestion)
* If not asked yet, ask it there.

If you want to post a problem/bug, to help us understand and resolve your issue
please check that you have provided the information below:

* Nuitka version, full Python version and platform (Windows, OSX, Linux ...)
* How did you install Nuitka and Python (pip, anaconda, deb, rpm, from source,
  what is the virtualenv ...), this is very important usually.
* If possible please supply a [Short, Self Contained, Correct, Example](http://sscce.org/)
  that demonstrates the issue i.e. a small piece of code which reproduces
  the issue and can be run without any other (or as few as possible)
  external dependencies.
* If this is a regression (used to work in an earlier version of Nuitka),
  please note what you know about that.

You also ought to do a quick check whether..

* the bug was already fixed in the branch for the next release, e.g. for the
  `develop` branch try pre-release packages out. Many times this is the case.

* if it was already reported and/or is maybe even being worked on already by
  checking open issues of the corresponding milestone, e.g. see [open and closed
  issues with "bug" label](https://github.com/kayhayen/Nuitka/issues?q=label%3Abug+).

## And finally

Welcome on board. Nuitka is an ambitious project. We are friendly. Join it now.
