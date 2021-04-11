import importlib.util
import os
import sys
from collections import defaultdict
from pathlib import Path


class RedirectingFinder:
    _redirections = {}
    _namespaces = defaultdict(list)

    @classmethod
    def map_module(cls, name, path):
        cls._redirections[name] = path

    @classmethod
    def add_namespace_path(cls, name, path):
        cls._namespaces[name].append(os.fspath(path))

    @classmethod
    def _get_paths(cls, name):
        paths = []
        for element in sys.path:
            # Does not handle non-filesystem entries
            path = Path(element) / name
            if path.is_dir():
                paths.append(path)
        paths.extend(cls._namespaces[name])
        return paths

    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        if "." in fullname:
            return None
        if path is not None:
            return None
        if fullname in cls._namespaces:
            spec = importlib.util.spec_from_loader(fullname, None)
            spec.submodule_search_locations = cls._get_paths(fullname)
        elif fullname in cls._redirections:
            redir = cls._redirections[fullname]
            spec = importlib.util.spec_from_file_location(fullname, redir)
        else:
            return None
        return spec

    @classmethod
    def install(cls):
        for f in sys.meta_path:
            if f == cls:
                break
        else:
            sys.meta_path.append(cls)
