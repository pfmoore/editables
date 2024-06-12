import importlib.abc
import importlib.machinery
import importlib.util
import sys
from types import ModuleType
from typing import Dict, Optional, Sequence, Union

ModulePath = Optional[Sequence[Union[bytes, str]]]


class RedirectingFinder(importlib.abc.MetaPathFinder):
    _redirections: Dict[str, str] = {}

    @classmethod
    def map_module(cls, name: str, path: str) -> None:
        cls._redirections[name] = path

    @classmethod
    def find_spec(
        cls, fullname: str, path: ModulePath = None, target: Optional[ModuleType] = None
    ) -> Optional[importlib.machinery.ModuleSpec]:
        try:
            redir = cls._redirections[fullname]
        except KeyError:
            return None
        spec = importlib.util.spec_from_file_location(fullname, redir)
        return spec

    @classmethod
    def install(cls) -> None:
        if cls not in sys.meta_path:
            sys.meta_path.append(cls)

    @classmethod
    def invalidate_caches(cls) -> None:
        # importlib.invalidate_caches calls finders' invalidate_caches methods,
        # and since we install this meta path finder as a class rather than an instance,
        # we have to override the inherited invalidate_caches method (using self)
        # as a classmethod instead
        pass
