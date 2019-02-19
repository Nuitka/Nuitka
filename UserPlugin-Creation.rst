
How To Create a User Plugin
============================

Background: Nuitka Standard and User Plugins
---------------------------------------------
User plugins are technically built and structured in the same way as Nuitka's
own *standard* plugins are. There also is no difference with respect to what
they can do. Both types are invoked via parameters in Nuitka's command line.
The difference is the invocation format:

* A standard plugin is invoked by ``--enable-plugin=<plugin_name>``. The string
  ``<plugin_name>`` is a unique identifier by which Nuitka identifies it. As
  soon as Nuitka has found the corresponding plugin, it will call its initialization
  method. Nuitka also has some standard plugins which are always activated.
  A standard plugin is represented by a Python script living in
  ``nuitka/plugins/standard``.
  Standard plugins also internally have an object which can issue warnings when
  it encounters situations looking like it is required.
* A user plugin is invoked by ``--user-plugin=</path/to/script.py>``. Nuitka
  will import the script and call its initialization method just like for a
  standard plugin. The plugin must have a non-empty string specified in its
  variable ``plugin_name``. It must also not equal one of the de-activated
  standard plugin strings. Best practice is filling it like so:
  ``plugin_name == __file__``. User plugins are always activated once they have
  been successfully loaded. They therefore have no mechanism that warns about
  not using them.

Example User Plugin
--------------------
This is a very simple user plugin. It will display source code lines of the
main program which contain calls to the buitlin ``math`` module, if an option
named "trace" is active::

    import os
    import sys
    from logging import info

    from nuitka import Options
    from nuitka.plugins.PluginBase import UserPluginBase

    class Usr_Plugin(UserPluginBase):

        plugin_name = __file__  # or __module__

        def __init__(self):
            # demo only: extract and display its list of options
            self.plugin_options = self.getPluginOptions()
            info(" '%s' options: %s" % (self.plugin_name, self.plugin_options))

            # check whether some specific option is set
            self.check = self.getPluginOptionBool("trace", False)
            info(" 'trace' is set to '%s'" % self.check)

            # do more init work here ...

        def onModuleSourceCode(self, module_name, source_code):
            # if this is the main script and tracing should be done ...
            if module_name == "__main__" and self.check:
                info("")
                info(" Calls to 'math' module:")
                for i, l in enumerate(source_code.splitlines()):
                    if "math." in l:
                        info(" %i: %s" % (i+1, l))
                info("")
            return source_code

Sample invocation line and output::

    $ python -m nuitka --standalone --user-plugin=user_plugin.py=trace script.py
    Nuitka:INFO: 'user_plugin.py' options: ['trace']
    Nuitka:INFO: 'trace' is set to True
    Nuitka:INFO:User plugin 'user_plugin.py' loaded.
    Nuitka:INFO:
    Nuitka:INFO: Calls to 'math' module:
    Nuitka:INFO: 125: print(math.sqrt(2))
    Nuitka:INFO:

    $

