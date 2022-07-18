#######################################
 Nuitka Standard Plugins Documentation
#######################################

.. |ups| replace::

   user plugins

.. |sps| replace::

   standard plugins

.. |ops| replace::

   optional standard plugins

****************************
 Background: Nuitka Plugins
****************************

Plugins are a feature to modify the way how Nuitka compiles Python
programs in extremely flexible ways.

Plugins can automatically include data files and additional shared
libraries, import modules which are not detectable by source code
analysis, modify or extend the to-be-compiled source code, gather
statistics, change Nuitka's parameter defaults and much more.

Any number of plugins may be used in each compilation.

Plugins come in two variants: **standard** plugins and **user** plugins.

User plugins are not part of the Nuitka package: they must be provided
otherwise. To use them in a compilation, Nuitka must be able to find
them using their path / filename. If |ups| are specified, Nuitka will
activate them **before** it activates any of its standard plugins.

Standard plugins are part of the Nuitka package and thus always
available.

Nuitka also differentiates between "mandatory" and "optional" |sps|.

**Mandatory** |sps| are always enabled and "invisible" to the user.
Their behaviour cannot be influenced other than by modifying them.

**Optional** |sps| must be enabled via the command line parameter
``--enable-plugin=name``, with an identifying string ``name``. Even when
not enabled however, |ops| can detect, whether their use might have been
"forgotten" and issue an appropriate warning.

Where appropriate, the behaviour of optional |sps| (like with |ups|) can
be controlled via *options* (see "Using Plugin Options").

*******************
 A Word of Caution
*******************

Almost all |ops| are relevant for standalone mode only. Specifying all
the right plugins is up to the user and critical for success: For
example, if you are using package *numpy* and forget to activate that
plugin, then your compile will

-  end with no error, but a warning about missing numpy support,

-  not generate a working binary.

Also:

-  |ups| are able to programmatically enable |ops|, the **reverse is not
   possible**. The user must know the requirements of his script and
   specify all appropriate |ops|, including any required *options* (see
   below).

-  There is currently no way to automatically react to
   interdependencies. For example, when compiling a script using the
   *tensorflow* package in standalone mode, you must enable (at least)
   **both**, the ``tensorflow`` **and** the ``numpy`` plugin.

-  Like every compiler, Nuitka cannot always decide, whether a script
   will **actually execute** an *import* statement. This knowledge must
   be provided by you, e.g. with PGO information that is going to be
   supported.

***********************************
 List of Optional Standard Plugins
***********************************

Create a list of available optional |sps| giving their identifier
together with a short description via ``--plugin-list``:

The following optional standard plugins are available in Nuitka:

.. code::

   anti-bloat            Patch stupid imports out of widely used library modules source codes.
   data-files
   data-hiding           Commercial: Hide program constant Python data from offline inspection of created binaries.
   datafile-inclusion    Commercial: Load file trusted file contents at compile time.
   dill-compat
   enum-compat
   ethereum              Commercial: Required for ethereum packages in standalone mode
   eventlet              Support for including 'eventlet' dependencies and its need for 'dns' package monkey patching
   gevent                Required by the gevent package
   gi                    Support for GI dependencies
   glfw                  Required for glfw in standalone mode
   implicit-imports
   multiprocessing       Required by Python's multiprocessing module
   numpy                 Required for numpy, scipy, pandas, matplotlib, etc.
   pbr-compat
   pkg-resources         Resolve version numbers at compile time.
   pmw-freezer           Required by the Pmw package
   pylint-warnings       Support PyLint / PyDev linting source markers
   pyqt5                 Required by the PyQt5 package.
   pyside2               Required by the PySide2 package.
   pyside6               Required by the PySide6 package for standalone mode.
   pyzmq                 Required for pyzmq in standalone mode
   tensorflow            Required by the tensorflow package
   tk-inter              Required by Python's Tk modules
   torch                 Required by the torch / torchvision packages
   traceback-encryption  Commercial: Encrypt tracebacks (de-Jong-Stacks).
   windows-service       Commercial: Create Windows Service files

.. note::

   This list is continuously growing and most likely out of date.

*****************************************
 Optional Standard Plugins Documentation
*****************************************

dill-compat
===========

-  Required by the *dill* module. Dill extends Python's pickle module
   for serializing and de-serializing objects.

-  Options: none.

eventlet
========

-  Required by the *eventlet* package. Eventlet is a concurrent
   networking library.

-  Options: none.

gevent
======

-  Required by the *gevent* package. Gevent is a coroutine-based Python
   networking library that uses greenlet to provide a high-level
   synchronous API.

-  Options: none.

numpy
=====

-  Required for *numpy, scipy, pandas, matplotlib, xarray, sklearn,
   skimage*, and most other scientific packages.

-  Options: Can disable some of the packages handled, e.g.
   ``--enable-plugin=numpy --noinclude-scipy --noinclude-matplotlib``
   which disables the handling to make these actually usable.

pmw-freezer
===========

-  Required by the *Pmw* package. Pmw is a toolkit for building
   high-level compound widgets.

-  Options: none.

pylint-warnings
===============

-  Support *PyLint* / *PyDev* linting source markers. Python static code
   analysis tools which help enforcing a coding standard.

-  Options: none

pyside2, pyside6, pyqt5
=======================

-  Required by the *PySide* and *PyQt* and GUI packages, only one can be
   activated at a time.

-  Options: With ``--include-qt-plugins`` you can select which Qt
   plugins to include. By default a relatively small set, called
   ``sensible`` that is defined in the code is include, but you can add
   more, and even ``all``, which will add a terrible amount of
   dependencies though. But without the proper Qt plugins, functionality
   of Qt might be broken, crashes can occur, or appearance can be
   inferior.

-  These plugins also inhibit other GUI frameworks from being included
   in standalone distributions.

tensorflow
==========

-  Required by the *tensorflow* package. TensorFlow is an open source
   machine learning framework for everyone. Note that this package
   requires *numpy* and potentially many other packages.

-  Options: none.

tk-inter
========

-  Required by Python's Tk modules.

-  Options: Can override the automatic detection of Tcl and Tk
   directories with ``--tk-library-dir`` and ``--tcl-library-dir`` but
   that should not be needed.

torch
=====

-  Required by the *torch* and *torchvision* packages. Tensors and
   Dynamic neural networks in Python with strong GPU acceleration.
   *Torchvision* requires *numpy*.

-  Options: none.
