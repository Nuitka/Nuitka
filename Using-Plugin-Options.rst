
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

A **whole new dimension of flexibility** can be added by using **options**
to control a plugin's functioning.

Option Specification
----------------------
**Standard plugins** are activated by the command line parameter
``--enable-plugin=<plugin_name>``. The parameter ``plugin_name`` must equal
the plugin's variable with the same name, so that Nuitka can identify it.

**User plugins** are activated by the command line parameter ``--user-plugin=<script.py>``,
where the parameter is a filename (-path) of a Python script implementing
the plugin protocol, i.e. it must be a class that inherits ``nuitka.plugins.PluginBase.UserPluginBase``
-- just like every Nuitka plugin.

Plugin options can be added by

* directly appending a "=" to its identifier or name, and

* specifying any string after the "="

The raw option string should normally not contain any white space. However,
depending on your platform, wrapping such a string in double quotes may also work.

Nuitka always passes a **Python list** to the plugin, which is determined as follows:

Assuming the command line parameter for a plugin called ``name`` contains
``--enable-plugin=name=raw`` (resp. ``--user-plugin=name=raw``), then method
``self.getPluginOptions()`` will deliver ``raw.split(',')``.
The following table aims to clarify this.

================== ==============================================
**Specification**  **Result**
================== ==============================================
``name``           ``[]`` (no option)
``name=``          ``['']`` (empty option)
``name=a,b,c``     ``['a', 'b', 'c']`` (3 options)
``name="a, b, c"`` ``['a', ' b', ' c']`` (3 options, some spaces)
================== ==============================================

While ``self.getPluginOptions()`` delivers the complete options list, you may also
check single option items via convenience method ``self.getPluginOptionBool("value", default)``.
Results:

* ``True`` if "value" is in the options list

* ``False`` if "novalue" is in the options list

* *default* else

* *exception* (exiting the compilation) if both, "value" and "novalue" are in the options list

Please note: there is no check for duplicate item values.

Remark
--------
Obviously, you can recover the original "raw" string by ``raw = ",".join(self.getPluginOptions())``
and then apply your own logic to it.

For example, if your plugin knows which format to expect, it could do things like

* ``my_option_dict = json.loads(raw)``, or

* ``my_option_list = raw.split(";")``.

Example
----------
To see a working example for a user plugin with ptions, consult `this <https://github.com/Nuitka/Nuitka/blob/develop/UserPlugin-Creation.rst>`__ document.
