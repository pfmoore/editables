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


def _init_py(abs_target: Union[str, os.PathLike]) -> str:
    abs_target = Path(abs_target)
    is_package = abs_target.name == "__init__.py"
    return f"""# Editables' module redirector
file = {repr(str(abs_target))}
__path__ = [{repr(str(abs_target.parent))}]

# Symlink for faster startup next time, inspired by `flit install -s`.
# Ignoring uninstallation for packages for now as it's complicated,
# but reinstalling without editability will overwrite the symlink
# and it'll be uninstalled fine after.
import os
try:
    {"os.symlink(__path__[0], __file__[:-3])" if is_package
     else "os.symlink(file, __file__ + '.new')\n"
     + "    os.rename(__file__ + '.new', __file__)"}
except OSError:
    __file__ = file # Please enable Developer Mode on Windows
del os
{"del __path__ # Is module not package" if not is_package
    else "__package__ = __name__\n" # Is package, so allow relative imports
    + "__spec__.submodule_search_locations = __path__"}

# Load from actual source of editable module
import io
try:
    with io.open_code(file) as file:
        file = file.read()
except OSError:
    file = ""
{"    raise # Module files should always exist" if not is_package
    else "pass # Support implicit namespace packages"}
del io

# Undo global namespace pollution before invoking actual module
def cleanup():
    global cleanup, file
    del cleanup, file
    return True

(lambda _file, _globals, _locals:
    cleanup() and _file and exec(_file, _globals, _locals))(file, globals(), locals())
"""


class EditableProject:
    def __init__(self, project_name: str, project_dir: Union[str, os.PathLike]) -> None:
        if not is_valid(project_name):
            raise ValueError(f"Project name {project_name} is not valid")
        self.project_name = normalize(project_name)
        self.bootstrap = f"_editable_impl_{self.project_name}"
        self.project_dir = Path(project_dir)
        self.redirections: Dict[str, str] = {}
        self.path_entries: List[Path] = []
        self.subpackages: Dict[str, Path] = {}
        self._files: Dict[str, str] = {}

    def make_absolute(self, path: Union[str, os.PathLike]) -> Path:
        return (self.project_dir / path).resolve()

    def map(self, name: str, target: Union[str, os.PathLike]) -> None:
        while name.startswith("."):
            name = name.removeprefix(".")
        if name == "__pycache__":
            return
        name = os.path.join(*name.split("."))
        abs_target = self.make_absolute(target)
        if abs_target.is_dir():
            abs_target = abs_target / "__init__.py"
        self._files[str(Path(name + ".py"))] = _init_py(abs_target)
        return
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
        with os.scandir(self.project_dir / dirname) as entries:
            for entry in entries:
                name = entry.name
                target = os.path.join(dirname, name)
                if entry.is_dir():
                    target = os.path.join(target, "__init__.py")
                elif entry.is_file() and name.endswith(".py"):
                    name = name[:-3]
                else:
                    continue
                self.map(name, target)

    def add_to_subpackage(self, package: str, dirname: Union[str, os.PathLike]) -> None:
        self.map(package, self.make_absolute(dirname) / "__init__.py")

    def files(self) -> Iterable[Tuple[str, str]]:
        yield from self._files.items()
        return
        yield f"{self.project_name}.pth", self.pth_file()
        if self.subpackages:
            for package, location in self.subpackages.items():
                yield self.package_redirection(package, location)
        if self.redirections:
            yield f"{self.bootstrap}.py", self.bootstrap_file()

    def dependencies(self) -> List[str]:
        deps = []
        if self.redirections:
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

    def bootstrap_file(self) -> str:
        bootstrap = [
            "from editables.redirector import RedirectingFinder as F",
            "F.install()",
        ]
        for name, path in self.redirections.items():
            bootstrap.append(f"F.map_module({name!r}, {path!r})")
        return "\n".join(bootstrap)
