# A Python library for creating "editable wheels"

This library supports the building of wheels which, when installed, will
expose packages in a local directory on `sys.path` in "editable mode". In
other words, changes to the package source will be  reflected in the package
visible to Python, without needing a reinstall.

## Usage

Suppose you want to build a wheel for your project `foo`. Your project is
located in the directory `/path/to/foo`. Under that directory, you have a
`src` directory containing your project, which is a package called `foo`
and a Python module called `bar.py`. So your directory structure looks like
this:

```
/path/to/foo
|
+-- src
|   +-- foo
|   |   +-- __init__.py
|   +-- bar.py
|
+-- setup.py
+-- other files
```

Build your wheel as follows:

```python
from editables import EditableProject

my_project = EditableProject("foo", "/path/to/foo")
my_project.add_to_path("src")

# Build a wheel however you prefer...
wheel = BuildAWheel()

# Add files to the wheel
for name, content in my_project.files():
    wheel.add_file(name, content)

# Record any runtime dependencies
for dep in my_project.dependencies():
    wheel.metadata.dependencies.add(dep)
```

The resulting wheel will, when installed, put the project `src` directory on
`sys.path` so that editing the original source will take effect without needing
a reinstall (i.e., as "editable" packages). The project is exposed on `sys.path`
by adding a single `.pth` file, named after the project, into the wheel.

For more details, including how to control what gets exposed more precisely, see
[the documentation](https://editables.readthedocs.io/en/latest/).

Note that this project doesn't build wheels directly. That's the responsibility
of the calling code.

## Python Compatibility

This project supports the same versions of Python as pip does. Currently
that is Python 3.6 and later, and PyPy3 (although we don't test against
PyPy).
