
Nuitka Standard Plugins Documentation
======================================

.. |ups| replace:: user plugins

.. |sps| replace:: standard plugins

.. |ops| replace:: optional standard plugins


Background: Nuitka Plugins
--------------------------------------
Plugins are a feature to modify the way how Nuitka compiles Python programs in
extremely flexible ways.

Plugins can automatically include data files and additional shared libraries,
import modules which are not detectable by source code analysis,
modify or extend the to-be-compiled source code, gather statistics, change
Nuitka's parameter defaults and much more.

Any number of plugins may be used in each compilation.

Plugins come in two variants: **standard** plugins and **user** plugins.

User plugins are not part of the Nuitka package: they must be provided otherwise. To use them in a compilation, Nuitka must be able to find them using their path / filename. If |ups| are specified, Nuitka will activate them **before** it activates any of its standard plugins.

Standard plugins are part of the Nuitka package and are therefore always available.

Nuitka also differentiates between "mandatory" and "optional" |sps|.

**Mandatory** |sps| are always enabled and "invisible" to the user. Their behaviour cannot be influenced other than by modifying them.

**Optional** |sps| must be enabled via the command line parameter ``--enable-plugin=name``, with an identifying string ``name``. Even when not enabled however, |ops| can detect, whether their use might have been "forgotten" and issue an appropriate warning.

Where appropriate, the behaviour of optional |sps| (like with |ups|) can be controlled via options (see "Using Plugin Options").

A Word of Caution
---------------------
Specifying required |ops| is up to the user. Specifically for standalone compilation, selecting the right |ops| is critical for success.

* While |ups| are able to programmatically enable |ops|, standard plugins technically **cannot do this**. The user must know the requirements of his script and specify all appropriate |ops|, including any required options (see below).
* There is currently no way to automatically react to interdependencies. For example, when compiling a script using the *tensorflow* package in ``--standalone`` mode, you must enable (at least) **both**, the ``tensorflow`` **and** the ``numpy`` plugin.
* Like every compiler, Nuitka cannot always decide, whether a script will **actually execute** an ``import`` statement. This knowledge must be provided to the compile command -- by specifying plugins and plugin options.

In `this <https://github.com/Nuitka/NUITKA-Utilities/tree/master/hinted-compilation>`_ repository folder you will find ways which automate the correct and complete specification of |ops| and their options.


List of Optional Standard Plugins
-------------------------------------------
Create a list of available optional |sps| giving their identifier together with a short description via ``--plugin-list``::

        The following optional standard plugins are available in Nuitka
  --------------------------------------------------------------------------------
   gevent           Required by the gevent package
   multiprocessing  Required by Python's multiprocessing module
   numpy            Required for numpy, scipy, pandas, matplotlib, etc.
   pmw-freezer      Required by the Pmw package
   pylint-warnings  Support PyLint / PyDev linting source markers
   qt-plugins       Required by the PyQt and PySide packages
   tensorflow       Required by the tensorflow package
   tk-inter         Required by Python's Tk modules on Windows
   torch            Required by the torch / torchvision packages

Optional Standard Plugins Documentation
-----------------------------------------
gevent
~~~~~~~
* Required by the *gevent* package.
* Options: none.

numpy
~~~~~~
* Required for *numpy, scipy, pandas, matplotlib, scikit-learn*, and many other packages.
* Options: specify any combination of ``scipy``, ``matplotlib`` or ``sklearn``, eg. ``--enable-plugin=numpy=scipy,matplotlib``.

pmw-freezer
~~~~~~~~~~~~
* Required by the *Pmw* package.
* Options: none.

pylint-warnings
~~~~~~~~~~~~~~~~
* Support *PyLint* / *PyDev* linting source markers.
* Options: none

qt-plugins
~~~~~~~~~~~
* Required by the *PyQt* and *PySide* packages.
* Options: ``sensible``, ``styles``, ``all``, **???**

tensorflow
~~~~~~~~~~~
* Required by the *tensorflow* package. Note that this package requires *numpy* and potentially many other packages or options.
* Options: none.

tk-inter
~~~~~~~~~
* Required by Python's Tk modules on Windows.
* Options: none.

torch
~~~~~~
* Required by the *torch*  and *torchvision* packages. *Torchvision* requires *numpy*.
* Options: none.
