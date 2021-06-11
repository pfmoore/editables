import re
from pathlib import Path

__all__ = (
    "EditableProject",
    "__version__",
)

__version__ = "0.2"


class EditableException(Exception):
    pass


class EditableProject:
    def __init__(self, project_name, project_dir):
        self.project_dir = Path(project_dir)
        self.redirections = {}
        self.path_entries = []

        # Ensure the name is a valid import
        self.project_name = re.sub(r"\W+", "_", project_name).lower()

    def make_absolute(self, path):
        return (self.project_dir / path).resolve()

    def map(self, name, target):
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

    def add_to_path(self, dirname):
        self.path_entries.append(self.make_absolute(dirname))

    def files(self):
        yield f"{self.project_name}.pth", self.pth_file()
        if self.redirections:
            yield f"_{self.project_name}.py", self.bootstrap_file()

    def dependencies(self):
        deps = []
        if self.redirections:
            deps.append("editables")
        return deps

    def pth_file(self):
        lines = []
        if self.redirections:
            lines.append(f"import _{self.project_name}")
        for entry in self.path_entries:
            lines.append(str(entry))
        return "\n".join(lines)

    def bootstrap_file(self):
        bootstrap = [
            "from editables.redirector import RedirectingFinder as F",
            "F.install()",
        ]
        for name, path in self.redirections.items():
            bootstrap.append(f"F.map_module({name!r}, {path!r})")
        return "\n".join(bootstrap)
