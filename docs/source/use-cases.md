# Use Cases

We will cover here the main supported use cases for editable installs,
including the recommended approaches for exposing the files to the
import system.

## Project directory installed "as is"

A key example of this is the recommended "`src` layout" for a project,
where a single directory (typically named `src`) is copied unchanged
into the target site-packages.

For this use case, the `project.add_to_path` method is ideal, making
the project directory available to the import system directly.

There are almost no downsides to this approach starting from the second run,
there will be a symbolic link in site-packages, so it will be recognised by
static analysis tools such as type checkers, and so editable installs created
using this method will be visible in such tools. For the first run, you can
mark the real project directory as a source directory if using PyCharm, or run
an `import` using the normal CPython if using Mypy.

Editables now avoids cluttering `sys.path` with `.pth` files. It will list the
modules in the directory at build time, then follows the logic of the next use
case. If you add a module, just rebuild the wheel.

## Project directory installed under an explicit package name

This is essentially the same as the previous use case, but rather than
listing the project directory and installing all its modules into
site-packages, one specified module is installed and can be renamed to
a particular package name. So, for example, if the project has a `src` directory
containing a package `foo` and a module `bar.py`, the user wants to install the
contents of `src` as `my.namespace.foo` and `my.namespace.bar`.

For this use case, the `project.add_to_subpackage` method is available.
This method creates the `my.namespace` package (by installing an `__init__.py`
file for it into site-packages) and gives that package a `__path__` attribute
pointing to the source directory to be installed under that package name. If
there is a preexisting `__init__.py` inside `my.namespace`, make sure to vendor
it, and call it from `src/__init__.py`.

Again, this approach uses core import system mechanisms, and so will have
few or no downsides at runtime. However on the first run, because this approach
relies on *runtime* manipulation of `__path__`, it will not be recognised by
static analysis tools. On the second run, there will be a symlink as stated
above.

## Installing part of a source directory

The most common case for this is a "flat" project layout, where the
package and module files to be installed are stored alongside project
files such as `pyproject.toml`. This layout is typically *not* recommended,
particularly for new projects, although older projects may be using this
type of layout for historical reasons.

The core import machinery does not provide a "native" approach supporting
*excluding* part of a directory like this, we need to `map` each module we want
to *include*. This function has changed to the previous use case's
`__init__.py`, and is no longer experimental. In fact, all the other use cases
are ease-of-use wrappers around this one. We removed the dependency on
executable `.pth` files, import hooks, and the `editables` module.

The `project.map` method allows mapping of either a single Python file, or
a Python package directory, to an explicit top-level name in the import system.
It does this by installing a `.pth` file and a Python module. The `.pth` file
simply runs the Python module, and the module installs the requested set of
mappings using an import hook exported by the `editables` module.

## Unsupported use cases

In addition to the above there are a number of use cases which are explicitly
**not** supported by this library. That is not to say that editable installs
cannot do these things, simply that the build backend will need to provide
its own support.

### Metadata changes

This library does not support dynamically changing installed project metadata
when the project source changes. Typically, a reinstall is needed in those
cases. A significant example of a metadata change is a change to the script
entry points, which affects what command-line executables are installed.

### Binary extensions

Binary extensions require a build step when the source code is changed. This
library does not support any sort of automatic rebuilding, nor does it
support automatic reinstallation of binaries.

The build backend may choose to expose the "working" version of the built
binary, for example by placing a symbolic link to the binary in a directory
that is visible to the import system as a result of `project.add_to_path`,
but that would need to be implemented by the backend.

### Mapping non-Python directories or files

The methods of an editable project are all intended explicitly for exposing
*Python code* to the import system. Other types of resource, such as data
files, are *not* supported, except in the form of package data physically
located in a Python package directory in the source.

### Combining arbitrary code into a package

The library assumes that a typical project layout, at least roughly, matches
the installed layout - and in particular that Python package directories are
"intact" in the source. Build backends can support more complex structures,
but in order to expose them as editable installs, they need to create some
form of "live" reflection of the final layout in a local directory (for
example by using symbolic links) and create the editable install using that
shadow copy of the source.

It is possible that a future version of this library may add support for
more complex mappings of this form, but that would likely require a
significant enhancement to the import hook mechanism being used, and would
be a major, backward incompatible, change. There are currently no plans for
such a feature, though.

### Overwriting packages

Overwriting modules is fine. Overwriting packages would require slowly
recursively removing the original package before installing the symlink, which
is important for performance. Moving it to a random name could fill up the disk
if it's not removed later. Therefore, we install a redirecting `.py` module
that can turn itself into a package if it chooses to set `__path__`. It installs
a symlink to speed up the second run. If it's a module, the symlink overwrites
the redirector, but symlinks can't overwrite packages. Python will silently
prefer to load existing packages rather than the redirecting module.
