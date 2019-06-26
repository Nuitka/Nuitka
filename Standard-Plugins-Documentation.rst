
Nuitka Standard Plugins Documentation
======================================

Background: Nuitka Plugins
--------------------------------------
Plugins are a feature to modify the way how Nuitka compiles Python programs in
extremely flexible ways.

Plugins can automatically include data files and additional shared libraries,
import modules not detectable by source code examination,
modify or extend the to-be-compiled source code, gather statistics, change
Nuitka's parameter defaults and much more.

Any number of plugins may be used in each compilation.

Plugins come in two variants: **standard** plugins and **user** plugins.

User plugins are not part of the Nuitka package: they must be provided otherwise. To use them in a compilation, Nuitka must be able to find them using their path / filename. If user plugins are specified, Nuitka will activate them **before** it activates any of its standard plugins.

.. |ups| replace:: user plugins

.. |sps| replace:: standard plugins

Standard plugins are part of the Nuitka package and are therefore always available.

Nuitka also differentiates between "mandatory" and "optional" |sps|.

**Mandatory** |sps| will be enabled automatically in every compilation and are thus "invisible" to the user. Their behaviour cannot be influenced other than by changing their source code.

**Optional** |sps| must be enabled via the command line parameter ``--enable-plugin=name``, with an identifying string ``name``. However, even when not enabled, optional |sps| can detect, whether their use might have been "forgotten" and issue an appropriate warning.

Where appropriate, the behaviour of optional |sps| (like with |ups|) can be controlled via options (see "Using Plugin Options").

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
   sklearn          Required by the scikit-learn package
   tensorflow       Required by the tensorflow package
   tk-inter         Required by Python's Tk modules on Windows
   torch            Required by the torch / torchvision packages


