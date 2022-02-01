#@+leo-ver=5-thin
#@+node:ekr.20210709045755.1: * @file ../scripts/wax_off.py
#@+<< docstring >>
#@+node:ekr.20210710050822.1: ** << docstring >>
"""
The "wax-off" utility.

Create stub files from existing annotation, then remove all function annotations.

So called because having created annotations in the python sources (wax-on)
we now want to remove them again (wax-off).

**Important**: In most cases it will be better to use make_stub_files (msb)
to create stub files. Unlike simplistic wax-on scripts, msb does a good job
of annotating the return values of functions.

Stub files provide the benefits of mypy with minimal clutter. The remaining
"clutter" (annotations of var types) turns out to be excellent
documentation.

**Tweaking the stub files**

The wax_off script knows very little about python. wax_off is just a
pattern matcher. wax_off moves def lines (and class lines) to the stub file
with the *existing* indentation. So mypy may complain about syntax errors
in the stub file:

1. If a class (like an exception class) has no methods, the class line
   should be followed by '...'. You must do that yourself.

2. If a function/method contains an inner def, mypy will also complain. You
   can just comment out those inner defs. They aren't needed anyway: mypy
   handles local attributes very well.

**Summary**

The wax_off script allows you to add full annotations for functions and
methods directly in the source files. When mypy is happy, just run wax_off
to move the def lines into stub files. wax_off then "declutters" the def
lines.
"""
#@-<< docstring >>
import argparse
import difflib
import glob
import os
import re
import sys

# Match class definitions.
class_pat = re.compile(r'^[ ]*class\s+[\w_]+.*?:', re.MULTILINE)

# Match function/method definitions.
def_pat = re.compile(r'^([ ]*)def\s+([\w_]+)\s*\((.*?)\)(.*?):', re.MULTILINE + re.DOTALL)

__version__ = 'wax_off.py version 1.0'

class WaxOff:
    diff = False
    trace = False
    #@+others
    #@+node:ekr.20210709065306.1: ** wax_off.do_file
    def do_file(self, input_fn):
        """Handle one file"""
        # Define output files.
        short_input_fn = os.path.basename(input_fn)
        stub_fn = os.path.join(self.output_directory, short_input_fn + 'i')
        new_fn = os.path.join(self.output_directory, short_input_fn)
        # Read the input file.
        with open(input_fn, 'r') as f:
            contents = f.read()
        # Find all the class defs.
        n = 0
        file_stubs, replacements = [], []
        for m in class_pat.finditer(contents):
            class_stub = m.group(0).rstrip() + '\n'
            file_stubs.append((m.start(), class_stub))
        # Find all the defs.
        for m in def_pat.finditer(contents):
            n += 1
            stub = f"{m.group(0)} ...\n"
            lws = m.group(1)
            name = m.group(2)
            args = self.stripped_args(m.group(3))
            # ret = m.group(4)
            stripped = f"{lws}def {name}({args}):"
            assert not stripped.startswith('\n'), stripped
            if 0:
                print(f"{n:>3} original: {m.group(0).rstrip()}")
                print(f"{n:>3}     stub: {stub.rstrip()}")
                print(f"{n:>3} stripped: {stripped}")
                print('')
            # Append the results.
            replacements.append((m.start(), m.group(0), stripped))
            file_stubs.append((m.start(), stub))
        # Dump the replacements:
        if 0:
            for i, data in enumerate(replacements):
                start, old, new = data
                print(i, start)
                print(f"{old!r}")
                print(f"{new!r}")
        # Sort the stubs.
        file_stubs.sort()
        # Dump the sorted stubs.
        if 0:
            for data in file_stubs:
                start, s = data
                print(s.rstrip())
        # Write the stub file.
        print(f"\nWriting {stub_fn}")
        with open(stub_fn, 'w') as f:
            f.write(''.join(z[1] for z in file_stubs))
        # Compute the new contents.
        new_contents = contents
        for data in reversed(replacements):
            start, old, new = data
            assert new_contents[start:].startswith(old), (start, old, new_contents[start:start+50])
            new_contents = new_contents[:start] + new + new_contents[start+len(old):]
        # Diff or write the file.
        if self.diff:  # Diff the old and new contents.
            lines = list(difflib.unified_diff(
                contents.splitlines(True), new_contents.splitlines(True),
                fromfile=input_fn, tofile=new_fn, n=0))
            print(f"Diff: {new_fn}")
            for line in lines:
                print(repr(line))
        else:  # Write the new file.
            print(f"Writing: {new_fn}")
            with open(new_fn, 'w') as f:
                f.write(new_contents)
        print(f"{len(replacements)} replacements")
    #@+node:ekr.20210709052929.3: ** wax_off.get_next_arg
    name_pat = re.compile(r'\s*([\w_]+)\s*')

    def get_next_arg(self, s, i):
        """
        Scan the next argument, retaining initializers, stripped of annotations.

        Return (arg, i):
        - arg: The next argument.
        - i:   The index of the character after arg.
        """
        assert i < len(s), (i, len(s))
        m = self.name_pat.match(s[i:])
        if not m:
            return (None, len(s))
        name = m.group(0).strip()
        i += len(m.group(0))
        if i >= len(s):
            return (name, i)
        if s[i] == ':':
            # Skip the annotation.
            i += 1
            j = self.skip_to_outer_delim(s, i, delims="=,")
            i = self.skip_ws(s, j)
        if i >= len(s):
            return name, i
        if s[i] == ',':
            return name, i + 1
        # Skip the initializer.
        assert s[i] == '=', (i, s[i:])
        i += 1
        j = self.skip_to_outer_delim(s, i, delims=",")
        initializer = s[i:j].strip()
        if j < len(s) and s[j] == ',':
            j += 1
        i = self.skip_ws(s, j)
        return f"{name}={initializer}", i

    #@+node:ekr.20210709102722.1: ** wax_off.main
    def main(self):
        """The main line of the wax_off script."""
        # Handle command-line options & set ivars.
        self.scan_options()
        # Handle each file.
        for fn in self.files:
            path = os.path.join(self.input_directory, fn)
            self.do_file(path)
    #@+node:ekr.20210709055018.1: ** wax_off.scan_options
    def scan_options(self):
        """Run commands specified by sys.argv."""

        def dir_path(s):
            if os.path.isdir(s):
                return s
            print(f"\nNot a directory: {s!r}")
            sys.exit(1)

        parser = argparse.ArgumentParser(
            description="wax_off.py: create stub files, then remove function annotations")
        add = parser.add_argument
        add('FILES', nargs='*', help='list of files or directories')
        add('-d', '--diff', dest='d', action='store_true', help='Show diff without writing files')
        add('-i', '--input-directory', dest='i_dir', metavar="DIR", type=dir_path, help='Input directory')
        add('-o', '--output-directory', dest='o_dir', metavar="DIR", type=dir_path, help='Output directory')
        add('-t', '--trace', dest='t', action='store_true', help='Show debug traces')
        add('-v', '--version', dest='v', action='store_true', help='show version and exit')
        args = parser.parse_args()
        # Handle all args.
        if args.v:
            print(__version__)
            sys.exit(0)
        # Set flags.
        self.diff = bool(args.d)
        self.trace = bool(args.t)
        # Compute directories. They are known to exist.
        self.input_directory = args.i_dir or os.getcwd()
        self.output_directory = args.o_dir or os.getcwd()
        # Get files.
        files = []
        for fn in args.FILES:
            path = os.path.join(self.input_directory, fn)
            files.extend(glob.glob(path))
        # Warn if files do not exist.
        self.files = []
        for path in files:
            if not path.endswith('.py'):
                print(f"Not a .py file: {path}")
            elif os.path.exists(path):
                self.files.append(path)
            else:
                print(f"File not found: {path}")
        # Trace, if requested.
        if self.trace:
            print('')
            print(f"  Input directory: {self.input_directory}")
            print(f" Output directory: {self.output_directory}")
            print('')
            print('Files...')
            for fn in self.files:
                print(f"  {fn}")
            print('')
        # Check the arguments.
        if not self.files:
            print('No input files')
            sys.exit(1)

    #@+node:ekr.20210709052929.4: ** wax_off.skip_to_outer_delim & helpers
    def skip_to_outer_delim(self, s, i, delims):
        """
        Skip to next *outer*, ignoring inner delimis contained in strings, etc.

        It is valid to reach the end of s before seeing the expected delim.

        Return i, the character after the delim, or len(s) if the delim has not been seen.
        """
        assert i < len(s), i
        # Type annotations only use [], but initializers can use anything.
        c_level, p_level, s_level = 0, 0, 0  # Levels for {}, (), []
        while i < len(s):
            ch = s[i]
            progress = i
            i += 1
            if ch in delims:
                if (c_level, p_level, s_level) == (0, 0, 0):
                    return i - 1  # Let caller handle ending delim.
            elif ch == '{':
                c_level += 1
            elif ch == '}':
                c_level -= 1
            elif ch == '(':
                p_level += 1
            elif ch == ')':
                p_level -= 1
            elif ch == '[':
                s_level += 1
            elif ch == ']':
                s_level -= 1
            elif ch in "'\"":
                i = self.skip_string(s, i-1)
            elif ch == "#":
                i = self.skip_comment(s, i-1)
            else:
                pass
            assert progress < i, (i, repr(s[i:]))
        assert (c_level, p_level, s_level) == (0, 0, 0), (c_level, p_level, s_level)
        return len(s)
    #@+node:ekr.20210709052929.5: *3* wax_off.skip_comment
    def skip_comment(self, s, i):
        """Scan forward to the end of a comment."""
        assert s[i] == '#'
        while i < len(s) and s[i] != '\n':
            i += 1
        return i
    #@+node:ekr.20210709052929.6: *3* wax_off.skip_string
    def skip_string(self, s, i):
        """Scan forward to the end of a string."""
        delim = s[i]
        i += 1
        assert(delim == '"' or delim == '\'')
        n = len(s)
        while i < n and s[i] != delim:
            if s[i] == '\\':
                i += 2
            else:
                i += 1
        assert i < len(s) and s[i] == delim, (i, delim)
        i += 1
        return i
    #@+node:ekr.20210709053410.1: *3* wax_off.skip_ws
    def skip_ws(self, s, i):
        while i < len(s) and s[i] in ' \t':
            i += 1
        return i
    #@+node:ekr.20210709052929.2: ** wax_off.stripped_args
    def stripped_args(self, s):
        """
        s is the argument list, without parens, possibly containing annotations.

        Return the argument list without annotations.
        """
        s = s.replace('\n',' ').replace('  ','').rstrip().rstrip(',')
        args, i = [], 0
        while i < len(s):
            progress = i
            arg, i = self.get_next_arg(s, i)
            if not arg:
                break
            args.append(arg)
            assert progress < i, (i, repr(s[i:]))
        return ', '.join(args)
    #@-others

if __name__ == '__main__':
    WaxOff().main()
#@-leo
