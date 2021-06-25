import os
from collections.abc import Iterator
from pathlib import Path

__all__ = (
    "EditableProject",
    "__version__",
)

__version__: str = "0.2"


class EditableException(Exception):
    pass


class EditableProject:
    project_name: str
    project_dir: Path
    redirections: "dict[str, str]"
    path_entries: "list[Path]"

    def __init__(
        self, project_name: str, project_dir: "str | os.PathLike[str]"
    ) -> None:
        self.project_name = project_name
        self.project_dir = Path(project_dir)
        self.redirections = {}
        self.path_entries = []

    def make_absolute(self, path: "str | os.PathLike[str]") -> Path:
        return (self.project_dir / path).resolve()

    def map(self, name: str, target: "str | os.PathLike[str]") -> None:
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

    def add_to_path(self, dirname: "str | os.PathLike[str]") -> None:
        self.path_entries.append(self.make_absolute(dirname))

    def files(self) -> "Iterator[tuple[str, str]]":
        yield f"{self.project_name}.pth", self.pth_file()
        if self.redirections:
            yield f"_{self.project_name}.py", self.bootstrap_file()

    def dependencies(self) -> "list[str]":
        deps = []
        if self.redirections:
            deps.append("editables")
        return deps

    def pth_file(self) -> str:
        lines = []
        if self.redirections:
            lines.append(f"import _{self.project_name}")
        for entry in self.path_entries:
            lines.append(str(entry))
        return "\n".join(lines)

    def bootstrap_file(self) -> str:
        bootstrap = [
            "from editables.redirector import RedirectingFinder as F",
            "F.install()",
        ]
        for name, path in self.redirections.items():
            bootstrap.append(f"F.map_module({name!r}, {path!r})")
        return "\n".join(bootstrap)
