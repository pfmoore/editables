import importlib.util
import os
import sys
from importlib.machinery import SOURCE_SUFFIXES, FileFinder, SourceFileLoader

location = ""  # location of replacement
excludes = ""  # excludes


class BackendImporter(FileFinder):
    """Allow imports included, disallow import excluded"""

    def find_spec(self, fullname, target=None):
        if any(fullname.startswith(m) for m in excludes):
            raise ImportError(fullname + " is excluded from packaging")
        return super().find_spec(fullname, target)


def finder(path):
    if path.startswith(os.path.join(location, __name__)):
        return BackendImporter(path, (SourceFileLoader, SOURCE_SUFFIXES))
    raise ImportError


def _bootstrap():
    sys.path_hooks.insert(0, finder)
    target = os.path.join(location, __name__)
    init = os.path.join(target, "__init__.py")
    spec = importlib.util.spec_from_file_location(__name__, init)
    module = importlib.util.module_from_spec(spec)
    sys.modules[__name__] = module
    spec.loader.exec_module(module)


_bootstrap()
