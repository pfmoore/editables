import base64
import importlib.abc
import importlib.util
import json
import re
import sys
import warnings
from pathlib import Path

# https://packaging.python.org/guides/packaging-namespace-packages/#pkgutil-style-namespace-packages
LEGACY_NAMESPACE_PACKAGE_INDICATOR = r"""__path__ = __import__\(["']pkgutil["']\)\.extend_path\(__path__, __name__\)"""


class Redirector:
    def __init__(self, project):
        self.project = project
        self.redirects = {}

    def redirect(self, target, import_name=None):
        target = Path(target)
        if import_name is None:
            import_name = target.stem

        redir = None
        if target.is_file():
            redir = target
        elif target.is_dir():
            init = target / "__init__.py"
            if init.is_file() and not re.search(LEGACY_NAMESPACE_PACKAGE_INDICATOR, init.read_text()):
                redir = init
            else:
                redir = [target]

        # Simple case, adding a new redirection
        if import_name not in self.redirects:
            self.redirects[import_name] = redir
            return

        # Redirecting a name that is already redirected
        existing = self.redirects[import_name]
        if not isinstance(existing, list):
            warnings.warn(f"Replacing redirection for package {import_name}")
            self.redirects[import_name] = redir
        elif not isinstance(redir, list):
            warnings.warn(f"Replacing redirection for namespace {import_name}")
            self.redirects[import_name] = redir
        else:
            # Add new paths to an existing namespace
            self.redirects[import_name].extend(redir)

    def serialise(self):
        return json.dumps(self.redirects, default=str)

    def files(self):
        yield (
            f"{self.project}.pth",
            " ".join(
                [
                    "import json, editables.redirector as R;",
                    "r = R.redirector;",
                    f"r.redirects.update(json.loads(r'''{self.serialise()}'''));",
                    "r.install()",
                ]
            ),
        )


class RedirectingFinder(importlib.abc.MetaPathFinder):
    def __init__(self):
        self.redirects = {}

    def find_spec(self, fullname, path, target=None):
        redir = self.redirects.get(fullname)
        spec = None
        print(f"{fullname} -> {redir}")
        if isinstance(redir, list):
            # Namespace package
            spec = importlib.util.spec_from_loader(fullname, None)
            if spec:
                spec.submodule_search_locations = redir
        else:
            spec = importlib.util.spec_from_file_location(fullname, str(redir))
        return spec

    def install(self):
        for hook in sys.meta_path:
            if hook == self:
                return
        sys.meta_path.append(self)


redirector = RedirectingFinder()
