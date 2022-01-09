# Contributing to Nuitka

This document aims to give an overview of how to contribute to Nuitka. It tries
to answer commonly asked questions regarding that, and to provide some insight

* If you plan on submitting an issue

  Please follow this [template](https://github.com/kayhayen/Nuitka/blob/develop/.github/ISSUE_TEMPLATE.md).

* If you want to open a pull request

  Make sure to read the information on this page but also have a look at our
  [pull request template](https://github.com/kayhayen/Nuitka/blob/develop/.github/PULL_REQUEST_TEMPLATE.md).

## Getting Started

* Read the [Nuitka User Manual](https://nuitka.net/doc/user-manual.html)
* Read the [Nuitka Developer Manual](https://nuitka.net/doc/developer-manual.html)
* Checkout the git repo of Nuitka additional docs and sources
* Join the [Gitter chat](https://gitter.im/Nuitka-chat/community)

## Submitting a Pull Request

Pull requests are great. Here's a quick guide:

1. Fork the repo on github.
2. Install the `pre-commit` git hook

   That is going to automatically format your code as described in the
   Developer Manual. For that you have to execute this:

   python misc/install-git-hooks.py

3. Make a new branch and base your new branch on `develop`.

4. Ideally add a test specific for your change to demonstrate it. Due to Nuitka

   testing being basically to compile the whole world, it's ok to not have one.
   But obviously if you fix something, it wasn't observed by that, it would be
   good to provide a reproducer.

5. Make the tests pass.

6. Push to your fork and submit a pull request against `nuitka:develop`

7. Wait for review

   Suggestions for improvements or alternative ideas may happen. Keep in mind that
   PR checklist items can be met after the pull request has been opened by adding
   more commits to the branch.

All the submitted pieces including potential data must be compatible with the
Apache License 2, which already says that once you are sending source, e.g.
via pull request, you automatically license it as that too.

## Submitting a Question

If you want to ask a question about a specific Nuitka aspect, please be kind
and first of all..

* Search for existing issues

  Consider [Github issues tagged as "question"](https://github.com/kayhayen/Nuitka/issues?q=label%3Aquestion)

* If not asked yet, ask it there.

## Submitting Issues

The issue template contains the guidance on how to properly support issues.

## And finally

Welcome on board. Nuitka is an ambitious project. We are friendly. Join it now.
