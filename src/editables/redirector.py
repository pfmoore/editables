import importlib.abc
import importlib.machinery
import importlib.util
import sys
from types import ModuleType
from typing import Dict, Optional, Sequence, Set, Union

ModulePath = Optional[Sequence[Union[bytes, str]]]


class RedirectingFinder(importlib.abc.MetaPathFinder):
    _redirections: Dict[str, str] = {}
    _parents: Set[str] = set()

    @classmethod
    def map_module(cls, name: str, path: str) -> None:
        cls._redirections[name] = path
        cls._parents.update(cls.parents(name))

    @classmethod
    def parents(cls, name):
        """
        Given a full name, generate all parents.

        >>> list(RedirectingFinder.parents('a.b.c.d'))
        ['a.b.c', 'a.b', 'a']
        """
        base, sep, name = name.rpartition('.')
        if base:
            yield base
            yield from cls.parents(base)

    @classmethod
    def find_spec(
        cls, fullname: str, path: ModulePath = None, target: Optional[ModuleType] = None
    ) -> Optional[importlib.machinery.ModuleSpec]:
        return cls.spec_from_parent(fullname) or cls.spec_from_redirect(fullname)

    @classmethod
    def spec_from_parent(
        cls, fullname: str
    ) -> Optional[importlib.machinery.ModuleSpec]:
        if fullname in cls._parents:
            return importlib.util.spec_from_loader(
                fullname,
                importlib.machinery.NamespaceLoader(
                    fullname,
                    path=[],
                    path_finder=cls.find_spec,
                ),
            )

    @classmethod
    def spec_from_redirect(
        cls, fullname: str
    ) -> Optional[importlib.machinery.ModuleSpec]:
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

    @classmethod
    def invalidate_caches(cls) -> None:
        # importlib.invalidate_caches calls finders' invalidate_caches methods,
        # and since we install this meta path finder as a class rather than an instance,
        # we have to override the inherited invalidate_caches method (using self)
        # as a classmethod instead
        pass
