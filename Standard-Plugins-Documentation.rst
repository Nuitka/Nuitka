
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

Standard plugins are part of the Nuitka package and thus always available.

Nuitka also differentiates between "mandatory" and "optional" |sps|.

**Mandatory** |sps| are always enabled and "invisible" to the user. Their behaviour cannot be influenced other than by modifying them.

**Optional** |sps| must be enabled via the command line parameter ``--enable-plugin=name``, with an identifying string ``name``. Even when not enabled however, |ops| can detect, whether their use might have been "forgotten" and issue an appropriate warning.

Where appropriate, the behaviour of optional |sps| (like with |ups|) can be controlled via *options* (see "Using Plugin Options").

A Word of Caution
---------------------
Almost all |ops| are relevant for standalone mode only. Specifying all the right plugins is up to the user and critical for success: for example. if you are using package *numpy* and forget to activate that plugin, then your compile will

    * end with no error, but a warning about missing numpy support,
    * not generate a working binary.


* |ups| are able to programmatically enable |ops|, the **reverse is not possible**. The user must know the requirements of his script and specify all appropriate |ops|, including any required *options* (see below).
* There is currently no way to automatically react to interdependencies. For example, when compiling a script using the *tensorflow* package in standalone mode, you must enable (at least) **both**, the ``tensorflow`` **and** the ``numpy`` plugin.
* Like every compiler, Nuitka cannot always decide, whether a script will **actually execute** an *import* statement. This knowledge must be provided by you via specifying plugins.

In `this <https://github.com/Nuitka/NUITKA-Utilities/tree/master/hinted-compilation>`_ repository folder you find help to address the above points of caution. These tools provide *runtime information* of your program to the Nuitka compiler, such that all required plugins are activated automatically, and only used packages are included.


List of Optional Standard Plugins
-------------------------------------------
Create a list of available optional |sps| giving their identifier together with a short description via ``--plugin-list``::

        The following optional standard plugins are available in Nuitka
--------------------------------------------------------------------------------
 dill-compat      Required by the dill module
 eventlet         Required by the eventlet package
 gevent           Required by the gevent package
 multiprocessing  Required by Python's multiprocessing module
 numpy            Required for numpy, scipy, pandas, matplotlib, etc.
 pmw-freezer      Required by the Pmw package
 pylint-warnings  Support PyLint / PyDev linting source markers
 qt-plugins       Required by the PyQt and PySide packages
 tensorflow       Required by the tensorflow package
 tk-inter         Required by Python's Tk modules
 torch            Required by the torch / torchvision packages

Optional Standard Plugins Documentation
-----------------------------------------
dill-compat
~~~~~~~~~~~~
* Required by the *dill* module. Dill extends Python's pickle module for serializing and de-serializing objects.
* Options: none.

eventlet
~~~~~~~~~
* Required by the *eventlet* package. Eventlet is a concurrent networking library.
* Options: none.

gevent
~~~~~~~
* Required by the *gevent* package. Gevent is a coroutine-based Python networking library that uses greenlet to provide a high-level synchronous API.
* Options: none.

numpy
~~~~~~
* Required for *numpy, scipy, pandas, matplotlib, xarray, sklearn, skimage*, and most other scientific packages.
* Options: "scipy", "matplotlib" if used. E.g. ``--enable-plugin=numpy=scipy,matplotlib``.

pmw-freezer
~~~~~~~~~~~~
* Required by the *Pmw* package. Pmw is a toolkit for building high-level compound widgets.
* Options: none.

pylint-warnings
~~~~~~~~~~~~~~~~
* Support *PyLint* / *PyDev* linting source markers. Python static code analysis tools which help enforcing a coding standard.
* Options: none

qt-plugins
~~~~~~~~~~~
* Required by the *PyQt* and *PySide* GUI packages.
* Options: "sensible", "styles", "qml", "xml", "all", where "sensible" means the default minimum set of Qt features.

tensorflow
~~~~~~~~~~~
* Required by the *tensorflow* package. TensorFlow is an open source machine learning framework for everyone. Note that this package requires *numpy* and potentially many other packages.
* Options: none.

tk-inter
~~~~~~~~~
* Required by Python's Tk modules.
* Options: none.

torch
~~~~~~
* Required by the *torch*  and *torchvision* packages. Tensors and Dynamic neural networks in Python with strong GPU acceleration. *Torchvision* requires *numpy*.
* Options: none.
