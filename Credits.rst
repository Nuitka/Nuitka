#########
 Credits
#########

*****************
 Nuitka Namesake
*****************

The most credits are deserved by my everloving and forgiving wife, who
bares with me for spending literally all my spare and other time
thinking of Nuitka.

See an image of her on Twitter and make her happy with donations and
Nuitka Commercial subscripts.

.. raw:: html

   <blockquote class="twitter-tweet" data-conversation="none"><p lang="en" dir="ltr">Nuitka is short for Annuitka, which is the nickname of my wife Anna who is Russian... here a recent shot with my son David.<br><br>I one day made her the compiler as a gift. Much better name than &quot;Py2C&quot;, right? <a href="https://t.co/9A3nod8CZ7">pic.twitter.com/9A3nod8CZ7</a></p>&mdash; Kay Hayen (@KayHayen) <a href="https://twitter.com/KayHayen/status/1028940741047930880?ref_src=twsrc%5Etfw">August 13, 2018</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

************************
 Contributors to Nuitka
************************

Thanks go to these individuals for their much-valued contributions to
Nuitka.

The order is sorted by time.

-  Li Xuan Ji: Contributed patches for general portability issue and
   enhancements to the environment variable settings.

-  Nicolas Dumazet: Found and fixed reference counting issues,
   ``import`` packages work, improved some of the English and generally
   made good code contributions all over the place, solved code
   generation TODOs, did tree building cleanups, core stuff.

-  Khalid Abu Bakr: Submitted patches for his work to support MinGW and
   Windows, debugged the issues, and helped me to get cross compile with
   MinGW from Linux to Windows. This was quite difficult stuff.

-  Liu Zhenhai: Submitted patches for Windows support, making the inline
   Scons copy actually work on Windows as well. Also reported import
   related bugs, and generally helped me make the Windows port more
   usable through his testing and information.

-  Christopher Tott: Submitted patches for Windows, and general as well
   as structural cleanups.

-  Pete Hunt: Submitted patches for macOS X support.

-  "ownssh": Submitted patches for built-ins module guarding, and made
   massive efforts to make high-quality bug reports. Also the initial
   "standalone" mode implementation was created by him.

-  Juan Carlos Paco: Submitted cleanup patches, created a Nuitka GUI and
   a Ninja IDE plugin for Nuitka. Both of no longer actively maintained
   though.

-  "Dr. Equivalent": Submitted the Nuitka Logo.

-  Johan Holmberg: Submitted patch for Python3 support on macOS X.

-  Umbra: Submitted patches to make the Windows port more usable, adding
   user provided application icons, as well as MSVC support for large
   constants and console applications.

-  David Cortesi: Submitted patches and test cases to make macOS port
   more usable, specifically for the Python3 standalone support of Qt.

-  Andrew Leech: Submitted github pull request to allow using "-m
   nuitka" to call the compiler. Also pull request to improve
   "bist_nuitka" and to do the registration.

-  Paweł K: Submitted github pull request to remove glibc from
   standalone distribution, saving size and improving robustness
   considering the various distributions.

-  Orsiris de Jong: Submitted github pull request to implement the
   dependency walking with ``pefile`` under Windows. Also provided the
   implementation of Dejong Stacks.

-  Jorj X. McKie: Submitted github pull requests with NumPy plugin to
   retain its accelerating libraries, and Tkinter to include the TCL
   distribution on Windows.

*************************
 Projects used by Nuitka
*************************

-  The `CPython project <https://www.python.org>`__

   Thanks for giving us CPython, which is the base of Nuitka. We are
   nothing without it.

-  The `GCC project <https://gcc.gnu.org>`__

   Thanks for not only the best compiler suite but also thanks for
   making it easy supporting to get Nuitka off the ground. Your compiler
   was the first usable for Nuitka and with very little effort.

-  The `Scons project <https://www.scons.org>`__

   Thanks for tackling the difficult points and providing a Python
   environment to make the build results. This is such a perfect fit to
   Nuitka and a dependency that will likely remain.

-  The `valgrind project <https://valgrind.org>`__

   Luckily we can use Valgrind to determine if something is an actual
   improvement without the noise. And it's also helpful to determine
   what's actually happening when comparing.

-  The `NeuroDebian project <https://neuro.debian.net>`__

   Thanks for hosting the build infrastructure that the Debian and
   sponsor Yaroslav Halchenko uses to provide packages for all Ubuntu
   versions.

-  The `openSUSE Buildservice <https://openbuildservice.org>`__

   Thanks for hosting this excellent service that allows us to provide
   RPMs for a large variety of platforms and make them available
   immediately nearly at release time.

-  The `MinGW64 project <https://mingw-w64.org>`__

   Thanks for porting the gcc to Windows. This allowed portability of
   Nuitka with relatively little effort.

-  The `Buildbot project <https://buildbot.net>`__

   Thanks for creating an easy to deploy and use continuous integration
   framework that also runs on Windows and is written and configured in
   Python code. This allows running the Nuitka tests long before release
   time.

-  The `isort project <https://timothycrosley.github.io/isort/>`__

   Thanks for making nice import ordering so easy. This makes it so easy
   to let your IDE do it and clean up afterward.

-  The `black project <https://github.com/ambv/black>`__

   Thanks for making a fast and reliable way for automatically
   formatting the Nuitka source code.
