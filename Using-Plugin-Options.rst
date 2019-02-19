
How To Use Plugin Options
============================

Background: Nuitka Plugins
--------------------------------------
Plugins are a feature to modify the way how Nuitka compiles Python programs in
extremely flexible ways.
Plugins automatically include data files and additional shared libraries,
import modules not detectable by source code examination,
modify or extend the to-be-compiled source code, gather statistics, change 
Nuitka's parameter defaults and much more.

Any number of plugins may be used in each compilation. A whole new dimension
of flexibility can be achieved by using options with a plugin that control its
functioning.

Option Specification
----------------------
**Standard plugins** are activated by the command line parameter ``--enable-plugin=<plugin_name>``. The parameter is reflected in the plugin
variable with the same name, and Nuitka identifies a standard plugin by it.

**User plugins** are activated by the command line parameter ``--user-plugin=<script.py>``,
where the parameter a filename (-path) of a Python script that implements the
plugin protocol, i.e. is a class that inherits ``nuitka.plugins.PluginBase.UserPluginBase`` -- just like every Nuitka plugin.

Plugin options can be added by
* appending a "=" immediately to its identifier, and
* specifying any string after the "="

The raw option string should normally not containing any white space. However,
depending on the platform, enclosing such a string in double quotes may lift
this restriction.

Nuitka always passes a **Python list** to the plugin, which is determined as follows:

Assuming the command line parameter for a plugin called ``name`` contains
``--enable-plugin=name=raw``, then ``self.getPluginOptions()`` contains
``raw.split(',')``. The following table shows some more examples.

================== ===================================
--enable-plugin=   result
================== ===================================
``name``           ``[]``
``name=``          ``['']``
``name=a,b,c``     ``['a', 'b', 'c']``
``name="a, b, c"`` ``['a', ' b', ' c']``
================== ===================================

All this works exactly the same for user plugins: append ``=raw`` to the plugin's
filename.

While ``self.getPluginOptions()`` delivers the complete options list, you may also
check single list items via utility method ``self.getPluginOptionBool("value", default)``. Results:
* *default* if "value" is not in the options list
* ``True`` if "value" is in the options list
* ``False`` if "novalue" is in the options list
* exception if both, "value" and "novalue" are in the options list

