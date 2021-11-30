###########################
 How To Use Plugin Options
###########################

****************************
 Background: Nuitka Plugins
****************************

Plugins are a feature to modify the way how Nuitka compiles Python
programs in extremely flexible ways.

Plugins can automatically include data files and additional shared
libraries, import modules not detectable by source code examination,
modify or extend the to-be-compiled source code, gather statistics,
change Nuitka's parameter defaults and much more.

Any number of plugins may be used in each compilation.

A **whole new dimension of flexibility** can be added by using
**options** to control a plugin's functioning.

**********************
 Option Specification
**********************

**Standard plugins** are activated by the command line parameter
``--enable-plugin=<plugin_name>``. The parameter ``plugin_name`` must
equal the plugin's variable with the same name, so that Nuitka can
identify it.

**User plugins** are activated by the command line parameter
``--user-plugin=<script.py>``, where the parameter is a filename (-path)
of a Python script implementing the plugin protocol, i.e. it must be a
class that inherits ``nuitka.plugins.PluginBase.UserPluginBase`` just
like every Nuitka plugin.

Plugin options can be added by overloading the method

.. code:: python

   @classmethod
   def addPluginCommandLineOptions(cls, group):
       ...  # add options to "group" here.

Here you extend the optparser group with any amount of options you
choose. Be careful with the ``dest`` names, try to make names that will
not collide with other plugins, as we have no per plugin namespace here.

*********
 Example
*********

To see a working example for a user plugin with options, consult `this
<https://github.com/Nuitka/Nuitka/blob/develop/UserPlugin-Creation.rst>`__
document.
