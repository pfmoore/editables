import importlib.util
import os
import sys
from importlib.machinery import SOURCE_SUFFIXES, FileFinder, SourceFileLoader

location = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
excludes = "foo.bar"


class BackendImporter(FileFinder):
    """Allow imports included, disallow import excluded"""

    def find_spec(self, fullname, target=None):
        if any(fullname.startswith(m) for m in excludes.split(",")):
            raise ImportError(f"{fullname} is excluded from packaging")
        return super().find_spec(fullname, target)


def finder(path):
    if path.startswith(os.path.join(location, __name__)):
        return BackendImporter(path, (SourceFileLoader, SOURCE_SUFFIXES))
    raise ImportError


sys.path_hooks.insert(0, finder)

name = __name__
location_of_replacement = location
target = os.path.join(location_of_replacement, name)
init = os.path.join(target, "__init__.py")
spec = importlib.util.spec_from_file_location(name, init)
module = importlib.util.module_from_spec(spec)
sys.modules[name] = module
spec.loader.exec_module(module)
