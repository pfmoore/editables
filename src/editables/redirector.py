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
        if "." in fullname:
            return None
        if path is not None:
            return None
        try:
            redir = cls._redirections[fullname]
        except KeyError:
            return None
        spec = importlib.util.spec_from_file_location(fullname, redir)
        return spec

    @classmethod
    def install(cls) -> None:
        for f in sys.meta_path:
            if f == cls:
                break
        else:
            sys.meta_path.append(cls)
