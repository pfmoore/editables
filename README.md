# A Python library for creating "editable wheels"

This library supports the building of wheels which, when installed, will
expose packages in a local directory on `sys.path` in "editable mode". In
other words, changes to the package source will be  reflected in the package
visible to Python, without needing a reinstall.

## Usage

Suppose you want to build a wheel that exposes the directory `dirname` as an
editable package when installed, equivalent to `pip install -e dirname`.
Build your wheel as follows:

```python
from editables import build_editable

for filename, content in build_editable(dirname):
    # Add content to your wheel, under the name filename
```

By default, this will expose every package in the given directory. You can
control what gets exposed using the `expose` and `hide` arguments of
`build_editable` (see the docstring for details).

This project doesn't build wheels directly. That's the responsibility of
the calling code.

## Python Compatibility

This project supports the same versions of Python as pip does. Currently
that is Python 3.6 and later, and PyPy3 (although we don't test against
PyPy).
