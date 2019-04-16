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

First, if the PR is directly related to an already existing issue (which has no
PR yet), drop a note in that issue before opening the PR.

 1. Fork the repo on github.
 2. Install the pre-commit hook that is going to automatically format your
    code as described in the Developer Manual.
 3. Make a new branch. For feature additions/changes base your new branch at
    `develop`, for pure bugfixes base your new branch at e.g. `master`.
 4. Ideally add a test specific for your change to demonstrate it. Due to Nuitka
    testing being basically to compile the whole world, it's ok to not have one.
    But obviously if you fix something, it wasn't observed by that, it would be
    good to provide a reproducer.
 5. Make the tests pass.
 6. Push to your fork and submit a pull request.
    - for feature branches set base branch to `nuitka:develop`
    - for bugfix branches set base branch to the latest maintenance branch, e.g. `nuitka:master`
 7. Wait for review, suggestions for improvements or alternative ideas may
    happen. Keep in mind that PR checklist items can be met after the pull
    request has been opened by adding more commits to the branch.

All the submitted pieces including potential data must be compatible with the
Apache License 2, which already says that you sending source, e.g. via pull
request, license it as that too.

## Submitting an Issue

If you want to ask a question about a specific Nuitka aspect, please first of all..

 * Search through [Github issues tagged as "question"](https://github.com/kayhayen/Nuitka/issues?q=label%3Aquestion)
 * Search the [nuitka-dev] mailing list archives, e.g.
   searching for term "standalone macos" via Google with search string "standalone site:https://www.freelists.org/archive may already reveal what you are looking for
 * If asked in neither forum, ask it there.

If you want to post a problem/bug, to help us understand and resolve your issue
please check that you have provided the information below:

*  Nuitka version, full Python version and platform (Windows, OSX, Linux ...)
*  How did you install Nuitka and Python (pip, anaconda, deb, rpm, from source,
   what is the virtualenv ...), this is very important usually.
*  If possible please supply a [Short, Self Contained, Correct, Example](http://sscce.org/)
      that demonstrates the issue i.e. a small piece of code which reproduces
      the issue and can be run without any other (or as few as possible)
      external dependencies.
*  If this is a regression (used to work in an earlier version of Nuitka),
   please note what you know about that.

You can also do a quick check whether..

 * the bug was already fixed in the branch for the next release, e.g. for the
   `develop` branch try pre-release packages out.

 * if it was already reported and/or is maybe even being worked on already by
   checking open issues of the corresponding milestone, e.g. see

   * [open and closed issues with "bug" label](
      https://github.com/kayhayen/Nuitka/issues?q=label%3Abug+).

## And finally

Welcome on board. Nuitka is an ambitious project. Join it now.
