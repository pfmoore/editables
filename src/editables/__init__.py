import os.path
from pathlib import Path
from typing import Dict, Iterable, Tuple, Union

__all__ = (
    "EditableProject",
    "__version__",
)

__version__ = "0.6"


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
    def __init__(
        self, _project_name: str, project_dir: Union[str, os.PathLike]
    ) -> None:
        self.project_dir = Path(project_dir)
        self._files: Dict[str, str] = {}

    def _make_absolute(self, path: Union[str, os.PathLike]) -> Path:
        return (self.project_dir / path).resolve()

    def map(self, name: str, target: Union[str, os.PathLike]) -> None:
        while name.startswith("."):
            name = name.removeprefix(".")
        if name == "__pycache__":
            return
        name = os.path.join(*name.split("."))
        abs_target = self._make_absolute(target)
        if abs_target.is_dir():
            abs_target = abs_target / "__init__.py"
        self._files[str(Path(name + ".py"))] = _init_py(abs_target)

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
        self.map(package, self._make_absolute(dirname) / "__init__.py")

    def files(self) -> Iterable[Tuple[str, str]]:
        return self._files.items()
