# The scope of this project

## Overview

The `editables` library provides a set of functions intended to allow
build backends to install an editable copy of a project source tree (the
*source*) into a Python environment (the *target*). It is *not* a general
tool allowing arbitrary mapping of code files to importable mdules. As a
consequence, there are a number of constraints on the scenarios supported
by the library:

* Source files must be laid out in a reasonable project structure.
* The target is a standard site-packages directory, managed by tools
  conforming to Python packaging standards.

Editable installations are a development convenience, and are not generally
intended for use in a production environment. While this doesn't directly
affect the functionality provided by this library, it *does* affect some of
the trade-offs made, particularly in terms of security (if an attacker has
access to a development environment, the developer has far greater issues
than whether or not their editable install mechanism can be exploited).

## Source Layouts

The library is designed to support common source layouts, and reasonable
variations of those layouts. While the functionality provided is general,
and can be used regardless of how the developer lays out their source code,
we do not guarantee that it will be possible to support every possible
arrangement of code files.

When raising a bug or feature request, users should be prepared to explain
what source layout they are using, and if it is not compatible with any of
the supported layouts described here, they should either be able to reproduce
their issue with a supported layout, or be prepared to request that their
layout is added to this list as a supported alternative.

### The `src` layout

This is by far the most common project layout, and is recommended for most
new Python projects. It is described in [the packaging guide]
(https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/).

In this layout, all of the project code is stored in a single directory within
the project repository, typically called `src`, and installation consists of
simply copying the content of the `src` directory to the target environment.

For this layout, the `add_to_path` method of an editable project should be
all that is needed in order to create an editable install.

### The "flat" layout

This is probably the second most common project layout, and is also described
in [the packaging guide]
(https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/).

It is generally considered inferior to the `src` layout because the project
code is mixed in with configuration files, tools and other scripts relating to
workflow, and other non-code files. However, it is attractive for single-file
projects, and for cases where being able to simply import the project from the
source directory, without an installation step, is useful.

For this layout, mapping the various top-level files and directories to their
expected import names is the recommended approach. However, if the project
avoids putting importable `.py` files in the workspace root directory, the
`add_to_path` method can be an acceptable (and simpler) alternative.

### Library code stored separately

Where a project has a significant amount of library code that is shipped as
part of the installed wheel, the developers may choose to keep that library
code in a separate directory within the project repository. For example,
consider the following project structure:

```
pyproject.toml
src
    myproject
        __init__.py
        cli
            __init__.py
            ...
        ...
libs
    utils
        __init__.py
    ...
```

When installed, the project should be importable as `import myproject`, with
`import myproject.cli`, and `import myproject.libs.utils` importing individual
subpackages. One important feature of this layout is that there is no `libs`
directory in the `src` tree - we only support grafting an external directory
into the module tree structure, *not* merging an external structure with content
held within the main source tree.

This layout is supported using the `add_to_subpackage` method. For the example
given above, the build backend should call
`editable_project.add_to_subpackage("myproject.libs", "<project root>/libs")`

### Multiple top level import names

This library supports projects that install multiple top-level names into the
target environment. This can involve a `src` directory with multiple packages in
it, or a number of directories and files exposed via `map`, or a combination of
both of these approaches.

However, it should be noted that we do *not* support installing a top-level name
that is already present, owned by another package. The Python import system does
technically allow top-level names to appear multiple times. The semantics of
this are subtle, though, and the implementation details of this library mean
that we don't always match the semantics of an actual install. Rather than try
to deal with these differences, we take the simple approach of saying "don't do
that".

## Notes on other structures

### The monorepo structure

A popular approach for developing Python code in larger projects is to use what
is called a "monorepo" - multiple projects maintained within a single VCS
repository. Whether you use a monorepo or not is not relevant to this project,
though, as the individual project directories are independent.

### Implicit namespace packages

Implicit namespace packages are directories that have no `__init__.py` file. The
import system treats them specially, considering them to be packages, but unlike
normal packages:

1. A namespace package is not considered to be "owned" by any one project.
2. If a namespace package appears multiple times in `sys.path`, the content is
   merged to produce a single combined import module.
3. The content of a namespace package is re-evaluated dynamically whenever an
   import occurs, rather than being cached at interpreter startup.

These behaviours are built in to the importlib path finder, and cannot be
customised by user code. As a result, we only support namespace packages in a
very limited number of cases.

1. When `add_to_path` is used, any namespace packages within the added path are
   handled normally.
2. When `map` is used, *with the self-replace method*, to register an import
   name that is in a namespace package, for example `ns.mypkg`, the containing
   namespace will work as normal.

Any other uses of namespace packages are not supported. Note in particular that
the import hook method of implementing `map` does *not* support namespace paths.
Import hooks cannot customise namespace package behaviour, as noted above.

## Additional notes

### Metadata changes

If a project's metadata is changed (for example, by editing the `pyproject.toml`
file), the metadata of the editable install will *not* change automatically.
These changes require a reinstall of the project to take effect.

One particular example here is adding or amending entry points to the project.
The modified entry points will not be available without a reinstall.

### Binary extensions

Native binary extensions are not supported. There are two key issues here:

1. Native code generally requires a compilation step, which needs a detailed
   understanding of the native build process. This knowledge is part of the
   build backend, and is not available to a general support library like this
   one.
2. The module mapping techniques used in this library have only been tested with
   pure Python modules. No attempt has been made to ensure that they work with
   binary extensions. In practice, methods that simply add entries to `sys.path`
   (the `add_to_path` and `add_to_subpackage` methods) will probably work, but
   other methods generally won't.

Build backends that handle native code can, of course, add their own support for
editable installs of native binary extensions.

### Filesystem operations

Because the editable import mechanisms (particularly the `map` method) break the
correspondence between filesystem structure and import package nesting, code
which uses filesystem operations to locate files relative to an imported module
may not behave as expected.

The `add_to_path` and `add_to_subpackage` methods, which simply manipulate
`sys.path`, should be fine as long as filesystem operations are constrained to
searching *within* the exposed module structure, and not reaching "upwards" in
the filesystem layout.

### Package resource access

The import hook strategy for `map` does not provide a resource loader as part of
its implementation. Nor does it support mapping anything other than Python
modules. As a result, `importlib.resources` is not supported. This could be
viewed as a bug, but given that the newer self replacing strategy handles the
resource API without needing special code, the recommended approach is simply to
switch to that strategy.

The self-replacing module strategy for `map` does not have this limitation, but
because it is only possible to map Python modules, and not data files, complex
maps are likely to not work as expected. Care should be taken in this case.

As usual, methods which work by manipulating `sys.path` (namely `add_to_path`
and `add_to_subpackage`) do not have these limitation, and package resource
access should work fine.

### Complex mapping of files

It is important to remember that this library is designed for exposing the
development sources of a Python package to an interpreter environment.
Generally, source layouts should match the structure of the modules being
developed fairly closely.

As a result, the methods in this library are *not* designed as a general module
mapping mechanism. Complex mappings are likely to cause issues, and the
recommended solution in such cases is to simplify your development source
layout.

Most projects should not need much more than a single `add_to_path` call, or
maybe one or two `map` calls.