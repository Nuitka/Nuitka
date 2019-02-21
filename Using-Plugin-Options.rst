
How To Use Plugin Options
============================

Background: Nuitka Plugins
--------------------------------------
Plugins are a feature to modify the way how Nuitka compiles Python programs in
extremely flexible ways.

Plugins can automatically include data files and additional shared libraries,
import modules not detectable by source code examination,
modify or extend the to-be-compiled source code, gather statistics, change
Nuitka's parameter defaults and much more.

Any number of plugins may be used in each compilation.

A whole new dimension of flexibility can be added by using **options**
with a plugin to control its functioning.

Option Specification
----------------------
**Standard plugins** are activated by the command line parameter ``--enable-plugin=<plugin_name>``. The parameter must equal the plugin's
variable with the same name, so that Nuitka can identify it.

**User plugins** are activated by the command line parameter ``--user-plugin=<script.py>``,
where the parameter is a filename (-path) of a Python script that implements
the plugin protocol, i.e. it must be a class that inherits ``nuitka.plugins.PluginBase.UserPluginBase`` -- just like every Nuitka plugin.

Plugin options can be added by
* appending "=" immediately to its identifier, and
* specifying any string after the "="

The raw option string should normally not contain any white space. However,
depending on the platform, enclosing such a string in double quotes may lift
this restriction.

Nuitka always passes a **Python list** to the plugin, determined as follows:

Assuming the command line parameter for a plugin called ``name`` contains
``--enable-plugin=name=raw``, then ``self.getPluginOptions()`` contains
``raw.split(',')``. The following table shows some examples.

================== ==============================================
--enable-plugin=   result
================== ==============================================
``name``           ``[]`` (no option)
``name=``          ``['']`` (empty option)
``name=a,b,c``     ``['a', 'b', 'c']`` (3 options)
``name="a, b, c"`` ``['a', ' b', ' c']`` (options with spaces)
================== ==============================================

All this works exactly the same for user plugins: append ``=raw`` to the plugin's
filename.

While ``self.getPluginOptions()`` delivers the complete options list, you may also
check single option items via convenience method ``self.getPluginOptionBool("value", default)``. Results:

* ``True`` if "value" is in the options list

* ``False`` if "novalue" is in the options list

* *default* else

* exception if both, "value" and "novalue" are in the options list

