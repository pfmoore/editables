import inspect
import os
from pathlib import Path

from . import install_hook

__all__ = (
    "build_editable",
    "__version__",
)

__version__ = "0.1"

_TEMPLATE = inspect.getsource(install_hook)


def build_editable(location, expose=None, hide=None):
    """Generate files that can be added to a wheel to expose packages from a directory.

    By default, every package (directory with __init__.py) in the supplied
    location will be exposed on sys.path by the generated wheel.

    Optional arguments:

    expose: A list of packages to include in the generated wheel
            (overrides the default behaviour).
    hide: A list of sub-packages of exposed packages that will be
          invisible in the generated wheel.

    Returns: a list of (name, content) pairs, specifying files that should
    be added to the generated wheel. Callers are responsible for building a
    valid wheel containing these files.
    """

    location = Path(location)

    if expose is None:
        expose = [pkg.parent.name for pkg in location.glob("*/__init__.py")]
    if hide is None:
        hide = []

    for pkg in expose:
        code = _TEMPLATE
        for of, to in {
            '""  # location of replacement': str(location),
            '""  # excludes': hide,
        }.items():
            code = code.replace(of, repr(to))
        code += "_bootstrap(){}".format(os.linesep)
        yield "{}.py".format(pkg), code
