# Changes

## Release 0.6

* Add a new "self_replace" strategy for `map` (and name the old
  strategy "import_hook"). Based on an idea by Daniel Tang in
  [#40](https://github.com/pfmoore/editables/pull/40).

## Release 0.5

* Fix a bug that broke `importlib.invalidate_caches`

## Release 0.4

* Add a new `add_to_subpackage` method.
* Add type annotations.
* Internal admin: Switch to nox for automation
* Internal admin: Switch to ruff for linting
* Internal admin: Switch from setuptools to flit_core

## Release 0.3

* Add documentation
* Validate and normalise project names
* Change: bootstrap file is now named `_editable_impl_<project>.py`
* Drop support for Python 3.6
* Add minimal release automation to update the version number
* Add this changelog
