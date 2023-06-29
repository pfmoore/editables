# Implementation Details

The key feature of a project that is installed in "editable mode" is that the
code for the project remains in the project's working directory, and what gets
installed into the user's Python installation is simply a "pointer" to that
code. The implication of this is that the user can continue to edit the project
source, and expect to see the changes reflected immediately in the Python
interpreter, without needing to reinstall.

The exact details of how such a "pointer" works, and indeed precisely how much
of the project is exposed to Python, are generally considered to be
implementation details, and users should not concern themselves too much with
how things work "under the hood". However, there are practical implications
which users of this library (typically build backend developers) should be aware
of.

The basic import machinery in Python works by scanning a list of directories
recorded in `sys.path` and looking for Python modules and packages in these
directories. (There's a *lot* more complexity behind the scenes, and interested
readers are directed to [the Python documentation](https://docs.python.org) for
more details). The initial value of `sys.path` is set by the interpreter, but
there are various ways of influencing this.

As part of startup, Python checks various "site directories" on `sys.path` for
files called `*.pth`. In their simplest form, `.pth` files contain a list of
directory names, which are *added* to `sys.path`. In addition, for more advanced
cases, `.pth` files can also run executable code (typically, to set up import
hooks to further configure the import machinery).

## Editables using `.pth` entries

The simplest way of setting up an editable project is to install a `.pth` file
containing a single line specifying the project directory. This will cause the
project directory to be added to `sys.path` at interpreter startup, making it
available to Python in "editable" form.

This is the approach which has been used by setuptools for many years, as part
of the `setup.py develop` command, and subsequently exposed by pip under the
name "editable installs", via the command `pip install --editable <project_dir>`.

In general, this is an extremely effective and low-cost approach to implementing
editable installs. It does, however, have one major disadvantage, in that it does
*not* necessarily expose the same packages as a normal install would do. If the
project is not laid out with this in mind, an editable install may expose importable
files that were not intended. For example, if the project root directory is added
directly to the `.pth` file, `import setup` could end up running the project's
`setup.py`! However, the recommended project layout, putting the Python source in
a `src` subdirectory (with the `src` directory then being what gets added to
`sys.path`) reduces the risk of such issues significantly.

The `editables` project implements this approach using the `add_to_path` method.

## Package-specific paths

If a package sets the `__path__` variable to a list of those directories, the
import system will search those directories when looking for subpackages or
submodules. This allows the user to "graft" a directory into an existing package,
simply by setting an appropriate `__path__` value.

The `editables` project implements this approach using the `add_to_subpackage` method.

## Import hooks

Python's import machinery includes an "import hook" mechanism which in theory
allows almost any means of exposing a package to Python. Import hooks have been
used to implement importing from zip files, for example. It is possible, therefore,
to write an import hook that exposes a project in editable form.

The `editables` project implements an import hook that redirects the import of a
package to a filesystem location specifically designated as where that package's
code is located. By using this import hook, it is possible to exercise precise
control over what is exposed to Python. For details of how the hook works,
readers should investigate the source of the `editables.redirector` module, part
of the `editables` package.

The `editables` project implements this approach for the `map` method. The
`.pth` file that gets written loads the redirector and calls a method on it
to add the requested mappings to it.

There are two downsides to this approach, as compared to the simple `.pth` file
mechanism - lack of support for implicit namespace packages, and the need for
runtime support code.

The first issue (lack of support for implicit namespace packages) is
unfortunate, but inherent in how Python (currently) implements the feature.
Implicit namespace package support is handled as part of how the core import
machinery does directory scans, and does not interact properly with the import
hook mechanisms. As a result, the `editables` import hook does not support
implicit namespace packages, and will probably never be able to do so without
help from the core Python implementation[^1].

The second issue (the need for runtime support) is more of an inconvenience than
a major problem. Because the implementation of the import hook is non-trivial,
it should be shared between all editable installs, to avoid conflicts between
import hooks, and performance issues from having unnecessary numbers of
identical hooks running. As a consequence, projects installed in this manner
will have a runtime dependency on the hook implementation (currently distributed
as part of `editables`, although it could be split out into an independent
project).

## Reserved Names

The `editables` project uses the following file names when building an editable
wheel. These should be considered reserved. While backends would not normally
add extra files to wheels generated using this library, they are allowed to do
so, as long as those files don't use any of the reserved names.

1. `<project_name>.pth`
2. `_editable_impl_<project_name>*.py`

Here, `<project_name>` is the name supplied to the `EditableProject` constructor,
normalised as described in [PEP 503](https://peps.python.org/pep-0503/#normalized-names),
with dashes replaced by underscores.

[^1]: The issue is related to how the same namespace can be present in multiple
      `sys.path` entries, and must be dynamically recomputed if the filesystem
      changes while the interpreter is running.
