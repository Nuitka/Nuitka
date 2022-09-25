#############################
 How To Create a User Plugin
#############################

**********************************************
 Background: Nuitka Standard and User Plugins
**********************************************

User plugins are technically built and structured in the same way as
Nuitka's own *standard* plugins are. There also is no difference with
respect to what they can do. Both types are invoked via parameters in
Nuitka's command line. The difference is the invocation format:

-  A standard plugin is invoked by ``--enable-plugin=<plugin_name>``.
   The string ``<plugin_name>`` is a unique identifier by which Nuitka
   identifies it. As soon as Nuitka has found the corresponding plugin,
   it will call its initialization method. Nuitka also has some standard
   plugins which are always activated. A standard plugin is represented
   by a Python script living in ``nuitka/plugins/standard``. Standard
   plugins also internally have an object which can issue warnings when
   it encounters situations looking like it is required.

-  A user plugin is invoked by ``--user-plugin=</path/to/script.py>``.
   Nuitka will import the script and call its initialization method just
   like for a standard plugin. The plugin must have a non-empty string
   specified in its variable ``plugin_name``. It must also not equal one
   of the de-activated standard plugin strings. Best practice is filling
   it with the filename, e.g. ``plugin_name == __file__``, because this
   allows providing it with options. User plugins are always activated
   once successfully loaded. They therefore have no mechanism to warn if
   not being used.

*********************
 Example User Plugin
*********************

This is a simple demo user plugin. It will display source code lines of
the main program if they contain calls to the ``math`` module, if an
option named "trace" is active:

.. code:: python

   import os
   import sys

   from nuitka import Options
   from nuitka.plugins.PluginBase import NuitkaPluginBase

   class NuitkaPluginMine(NuitkaPluginBase):
       # Derive from filename, but can and should also be explicit.
       plugin_name = __name__.split(".")[-1]

       def __init__(self, trace_my_plugin):
           # demo only: extract and display my options list
           # check whether some specific option is set

           self.check = trace_my_plugin
           self.info(" 'trace' is set to '%s'" % self.check)

           # do more init work here ...

       @classmethod
       def addPluginCommandLineOptions(cls, group):
           group.add_option(
               "--trace-my-plugin",
               action="store_true",
               dest="trace_my_plugin",
               default=False,
               help="This is show in help output."
           )

       def onModuleSourceCode(self, module_name, source_code):
           # if this is the main script and tracing should be done ...
           if module_name == "__main__" and self.check:
               self.info("")
               self.info(" Calls to 'math' module:")
               for i, l in enumerate(source_code.splitlines()):
                   if "math." in l:
                       self.info(" %i: %s" % (i+1, l))
               self.info("")
           return source_code

Sample invocation line and output:

.. code:: bash

   python -m nuitka --standalone --user-plugin=user_plugin.py=trace script.py

.. code::

   Nuitka:INFO: 'user_plugin.py' options: ['trace']
   Nuitka:INFO: 'trace' is set to True
   Nuitka:INFO:User plugin 'user_plugin.py' loaded.
   Nuitka:INFO:
   Nuitka:INFO: Calls to 'math' module:
   Nuitka:INFO: 125: print(math.sqrt(2))
   Nuitka:INFO:

*************************
 Nuitka Options Overview
*************************

About 60 methods are available to access option information for the
current Nuitka execution. Import the ``Options`` module (``from nuitka
import Options``) and use one of the following.

Please note that ``str`` results may return ``None``. Except very few,
the methods have no argument.

+--------------------------------------+-----------------------------------------------------------------------------------+
| **Method**                           | **Description**                                                                   |
+======================================+===================================================================================+
| assumeYesForDownloads                | *bool* = ``--assume-yes-for-downloads``                                           |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isExperimental                       | *bool*, check for items of ``--experimental=``                                    |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getFileReferenceMode                 | *str*, one of ``runtime``, ``original`` or ``frozen`` (``--file-reference-mode``) |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getIconPaths                         | *list*, values of icon options                                                    |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getJobLimit                          | *int*, value of ``--jobs`` / ``-j`` or number of CPU kernels                      |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getMainArgs                          | *tuple*, arguments following the optional arguments                               |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getMsvcVersion                       | *str*, value of ``--msvc``                                                        |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getMustIncludeModules                | *list*, items of ``--include-module=``                                            |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getMustIncludePackages               | *list*, items of ``--include-package=``                                           |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getOutputDir                         | *str*, value of ``--output-dir``                                                  |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getOutputFilename                    | *str*, value of ``-o``                                                            |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getOutputPath(path)                  | *str*, os.path.join(getOutputDir(), path)                                         |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getPluginsDisabled                   | *tuple*, items of ``--disable-plugin=``                                           |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getPluginsEnabled                    | *tuple*, enabled plugins (including user plugins)                                 |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getPluginOptions(plugin_name)        | *list*, options for specified plugin                                              |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getPositionalArgs                    | *tuple*, command line positional arguments                                        |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getPythonFlags                       | *list*, value of ``--python-flag``                                                |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getPythonPathForScons                | *str*, value of ``--python-for-scons``                                            |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getShallFollowExtra                  | *list*, items of ``--include-plugin-directory=``                                  |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getShallFollowExtraFilePatterns      | *list*, items of ``--include-plugin-files=``                                      |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getShallFollowInNoCase               | *list*, items of ``--nofollow-import-to=``                                        |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getShallFollowModules                | *list*, items of ``--follow-import-to=``                                          |
+--------------------------------------+-----------------------------------------------------------------------------------+
| getUserPlugins                       | *tuple*, items of ``--user-plugin=``                                              |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isAllowedToReexecute                 | *bool* = **not** ``--must-not-re-execute``                                        |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isClang                              | *bool* = ``--clang``                                                              |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isDebug                              | *bool* = ``--debug`` or ``--debugger``                                            |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isExperimental("feature")            | *bool* = ``--experimental=feature``                                               |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isFullCompat                         | *bool* = ``--full-compat``                                                        |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isLto                                | *bool* = ``--lto``                                                                |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isMingw64                            | *bool* = ``--mingw64``                                                            |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isProfile                            | *bool* = ``--profile``                                                            |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallUsePythonDebug                  | *bool* = ``--python-debug`` or ``sys.flags.debug``                                |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isRemoveBuildDir                     | *bool* = ``--remove-output``                                                      |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isShowInclusion                      | *bool* = ``--show-modules``                                                       |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isShowMemory                         | *bool* = ``--show-memory``                                                        |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isShowProgress                       | *bool* = ``--show-progress``                                                      |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isShowScons                          | *bool* = ``--show-scons``                                                         |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isStandaloneMode                     | *bool* = ``--standalone``                                                         |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isUnstripped                         | *bool* = ``--unstripped`` or ``--profile``                                        |
+--------------------------------------+-----------------------------------------------------------------------------------+
| isVerbose                            | *bool* = ``--verbose``                                                            |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallClearPythonPathEnvironment      | *bool* = **not** ``--execute-with-pythonpath``                                    |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallCreatePyiFile                   | *bool* = **not** ``--no-pyi-file``                                                |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallDetectMissingPlugins            | *bool* = **not** ``--plugin-no-detection``                                        |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallDisableConsoleWindow            | *bool* = ``--win-disable-console``                                                |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallExecuteImmediately              | *bool* = ``--run``                                                                |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallExplainImports                  | *bool* = ``--explain-imports``                                                    |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallFollowAllImports                | *bool* = ``--follow-imports``                                                     |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallFollowNoImports                 | *bool* = ``--nofollow-imports``                                                   |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallListPlugins                     | *bool* = ``--plugin-list``                                                        |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallMakeModule                      | *bool* = ``--module``                                                             |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallNotDoExecCCompilerCall          | *bool* = ``--generate-c-only``                                                    |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallNotStoreDependsExeCachedResults | *bool* = ``--disable-dll-dependency-cache``                                       |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallNotUseDependsExeCachedResults   | *bool* = ``--disable-dll-dependency-cache`` or                                    |
|                                      | ``--force-dll-dependency-cache-update``                                           |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallOnlyExecCCompilerCall           | *bool* = ``--recompile-c-only``                                                   |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallRunInDebugger                   | *bool* = ``--debug``                                                              |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallTraceExecution                  | *bool* = ``--trace-execution``                                                    |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallWarnImplicitRaises              | *bool* = ``--warn-implicit-exceptions``                                           |
+--------------------------------------+-----------------------------------------------------------------------------------+
| shallWarnUnusualCode                 | *bool* = ``--warn-unusual-code``                                                  |
+--------------------------------------+-----------------------------------------------------------------------------------+
