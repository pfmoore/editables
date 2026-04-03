# Changes

## Release 0.6

* All 3 methods now wrap `project.map`
* All exception-causing restrictions were removed
* `*.pth` is no longer used
* All methods use `mymodule.py` files that then basically `execfile()`
* It may also create symlinks for performance and static analysis when available

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
