import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Union

__all__ = (
    "EditableProject",
    "__version__",
)

__version__ = "0.5"


# Check if a project name is valid, based on PEP 426:
# https://peps.python.org/pep-0426/#name
def is_valid(name: str) -> bool:
    return (
        re.match(r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", name, re.IGNORECASE)
        is not None
    )


# Slightly modified version of the normalisation from PEP 503:
# https://peps.python.org/pep-0503/#normalized-names
# This version uses underscore, so that the result is more
# likely to be a valid import name
def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "_", name).lower()


class EditableException(Exception):
    pass


class EditableProject:
    def __init__(self, project_name: str, project_dir: Union[str, os.PathLike]) -> None:
        if not is_valid(project_name):
            raise ValueError(f"Project name {project_name} is not valid")

        # TODO: Using a public attribute with a magic string value to determine
        #       the preferred implementation for map() is *not* a good approach.
        #       Work out something better!
        self.map_method = "import_hook"  # or "self_replace"

        self.project_name = normalize(project_name)
        self.bootstrap = f"_editable_impl_{self.project_name}"
        self.project_dir = Path(project_dir)
        self.redirections: Dict[str, str] = {}
        self.path_entries: List[Path] = []
        self.subpackages: Dict[str, Path] = {}

    def make_absolute(self, path: Union[str, os.PathLike]) -> Path:
        return (self.project_dir / path).resolve()

    def map(self, name: str, target: Union[str, os.PathLike]) -> None:
        if "." in name:
            raise EditableException(
                f"Cannot map {name} as it is not a top-level package"
            )
        abs_target = self.make_absolute(target)
        if abs_target.is_dir():
            abs_target = abs_target / "__init__.py"
        if abs_target.is_file():
            self.redirections[name] = str(abs_target)
        else:
            raise EditableException(f"{target} is not a valid Python package or module")

    def add_to_path(self, dirname: Union[str, os.PathLike]) -> None:
        self.path_entries.append(self.make_absolute(dirname))

    def add_to_subpackage(self, package: str, dirname: Union[str, os.PathLike]) -> None:
        self.subpackages[package] = self.make_absolute(dirname)

    def files(self) -> Iterable[Tuple[str, str]]:
        yield f"{self.project_name}.pth", self.pth_file()
        if self.subpackages:
            for package, location in self.subpackages.items():
                yield self.package_redirection(package, location)
        if self.redirections:
            if self.map_method == "import_hook":
                yield f"{self.bootstrap}.py", self.bootstrap_file()
            else:
                for name, target in self.redirections.items():
                    yield f"{name}.py", self.self_replacer(target)

    def dependencies(self) -> List[str]:
        deps = []
        if self.redirections and self.map_method == "import_hook":
            deps.append("editables")
        return deps

    def pth_file(self) -> str:
        lines = []
        if self.redirections:
            lines.append(f"import {self.bootstrap}")
        for entry in self.path_entries:
            lines.append(str(entry))
        return "\n".join(lines)

    def package_redirection(self, package: str, location: Path) -> Tuple[str, str]:
        init_py = package.replace(".", "/") + "/__init__.py"
        content = f"__path__ = [{str(location)!r}]"
        return init_py, content

    def self_replacer(self, target: str) -> str:
        replacer = [
            "import importlib.util",
            "import sys",
            "",
            "def import_from_path(module_name, file_path):",
            "    spec = importlib.util.spec_from_file_location(module_name, file_path)",
            "    module = importlib.util.module_from_spec(spec)",
            "    sys.modules[module_name] = module",
            "    spec.loader.exec_module(module)",
            "",
            f"import_from_path(__name__, {target!r})",
        ]
        return "\n".join(replacer)

    def bootstrap_file(self) -> str:
        bootstrap = [
            "from editables.redirector import RedirectingFinder as F",
            "F.install()",
        ]
        for name, path in self.redirections.items():
            bootstrap.append(f"F.map_module({name!r}, {path!r})")
        return "\n".join(bootstrap)
