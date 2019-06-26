
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

.. |sps| replace:: standard plugins

Standard plugins are part of the Nuitka package and are therefore always available.

Nuitka also differentiates between "mandatory" and "optional" |sps|. **Mandatory** |sps| will be enabled automatically in every compilation, **optional** |sps| must be enabled via the command line parameter ``--enable-plugin``.

Unlike user plugins, standard plugin activation happens via a unique name (string), which is coded in its source.

