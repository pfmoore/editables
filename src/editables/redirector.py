import base64
import importlib.abc
import importlib.util
import json
import sys
from pathlib import Path


class Redirector:
    def __init__(self, project):
        self.project = project
        self.redirects = {}
        self.namespaces = {}

    def redirect(self, mod, target):
        assert "." not in mod
        # TODO: What if mod is already redirected?

        target = Path(target)
        if target.is_file():
            self.redirects[mod] = target
            return

        init = target / "__init__.py"
        if init.is_file():
            self.redirects[mod] = init
        else:
            if mod in self.namespaces:
                self.namespaces.append(target)
            else:
                self.namespaces[mod] = [target]

    def serialise(self):
        return base64.b64encode(
            json.dumps([self.redirects, self.namespaces], default=str).encode("utf-8")
        ).decode("ascii")

    def files(self):
        yield (
            f"{self.project}.pth",
            " ".join(
                [
                    "import editables.redirector;",
                    "r = editables.redirector.redirector;",
                    f"r.load('{self.serialise()}');",
                    "r.install()",
                ]
            ),
        )


class RedirectingFinder(importlib.abc.MetaPathFinder):
    def __init__(self):
        self.redirects = {}
        self.namespaces = {}

    def load(self, data):
        self.redirects, self.namespaces = json.loads(
            base64.b64decode(data).decode("utf-8")
        )

    def find_spec(self, fullname, path, target=None):
        redir = self.redirects.get(fullname)
        ns = self.namespaces.get(fullname)
        spec = None
        if redir:
            spec = importlib.util.spec_from_file_location(fullname, str(redir))
        elif ns:
            # Namespace package
            spec = importlib.util.spec_from_loader(fullname, None)
            if spec:
                spec.submodule_search_locations = ns
        return spec

    def install(self):
        for hook in sys.meta_path:
            if hook == self:
                return
        sys.meta_path.append(self)


redirector = RedirectingFinder()
