from pathlib import Path
TEMPLATE = """\
import os
import sys
import importlib.util
from importlib.machinery import FileFinder, SourceFileLoader, SOURCE_SUFFIXES

name = __name__
location_of_replacement = {location!r}
excludes = {excludes!r}.split(",")

class BackendImporter(FileFinder):
    \"""Allow imports included, disallow import excluded\"""

    def find_spec(self, fullname, target=None):
        if any(fullname.startswith(m) for m in excludes.split(",")):
            raise ImportError(fullname + " is excluded from packaging")
        return super().find_spec(fullname, target)

def finder(path):
    if path.startswith(os.path.join(location, __name__)):
        return BackendImporter(path, (SourceFileLoader, SOURCE_SUFFIXES))
    raise ImportError

sys.path_hooks.insert(0, finder)

target = os.path.join(location_of_replacement, name)
init = os.path.join(target, "__init__.py")
spec = importlib.util.spec_from_file_location(name, init)
module = importlib.util.module_from_spec(spec)
sys.modules[name] = module
spec.loader.exec_module(module)
"""

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

    if expose:
        for e in expose:
            if not (location / e / "__init__.py").is_file():
                raise ValueError("{} is not a package in {}".format(e, location))
    else:
        expose = [pkg.parent.name for pkg in location.glob("*/__init__.py")]

    if hide:
        for h in hide:
            if not any(h.startswith(e) for e in expose):
                raise ValueError("{} is not part of an exposed package".format(h))

    for e in expose:
        h = [h for h in hide if h.startswith(e)]
        code = TEMPLATE.format(location=location, excludes=",".join(h))
        yield (e + ".py", code)