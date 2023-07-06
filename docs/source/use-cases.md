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

There are almost no downsides to this approach, as it is using core
import system mechanisms to manage `sys.path`. Furthermore, the method
is implemented using `.pth` files, which are recognised by static analysis
tools such as type checkers, and so editable installs created using this
method will be visible in such tools.

## Project directory installed under an explicit package name

This is essentially the same as the previous use case, but rather than
installing the project directory directly into site-packages, it is
installed under a partocular package name. So, for example, if the
project has a `src` directory containing a package `foo` and a module
`bar.py`, the requirement is to install the contents of `src` as
`my.namespace.foo` and `my.namespace.bar`.

For this use case, the `project.add_to_subpackage` method is available.
This method creates the `my.namespace` package (by installing an `__init__.py`
file for it into site-packages) and gives that package a `__path__` attribute
pointing to the source directory to be installed under that package name.

Again, this approach uses core import system mechanisms, and so will have
few or no downsides at runtime. However, because this approach relies on
*runtime* manipulation of `sys.path`, it will not be recognised by static
analysis tools.

## Installing part of a source directory

The most common case for this is a "flat" project layout, where the
package and module files to be installed are stored alongside project
files such as `pyproject.toml`. This layout is typically *not* recommended,
particularly for new projects, although older projects may be using this
type of layout for historical reasons.

The core import machinery does not provide a "native" approach supporting
excluding part of a directory like this, so custom import hooks are needed
to implement it. At the time of writing, all such custom hook implementations
have limitations, and should be considered experimental. As a result, build
backends should *always* prefer one of the other implementation methods when
available.

The `project.map` method allows mapping of either a single Python file, or
a Python package directory, to an explicit top-level name in the import system.
It does this by installing a `.pth` file and a Python module. The `.pth` file
simply runs the Python module, and the module installs the requested set of
mappings using an import hook exported by the `editables` module.

Downsides of this approach are:

1. The approach depends on the ability to run executable code from a `.pth`
   file. While this is a supported capability of `.pth` files, it is
   considered a risk, and there have been proposals to remove it. If that
   were to happen, this mechanism would no longer work.
2. It adds a *runtime* dependency on the `editables` module, rather than
   just a build-time dependency.
3. The import hook has known limitations when used with implicit namespace
   packages - there is [a CPython issue](https://github.com/python/cpython/issues/92054)
   discussing some of the problems.

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
