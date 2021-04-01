import contextlib
import site
import sys

import pytest

from editables.redirector import Redirector


@contextlib.contextmanager
def save_import_state():
    orig_modules = set(sys.modules.keys())
    orig_path = list(sys.path)
    orig_meta_path = list(sys.meta_path)
    orig_path_hooks = list(sys.path_hooks)
    orig_path_importer_cache = sys.path_importer_cache
    try:
        yield
    finally:
        remove = [key for key in sys.modules if key not in orig_modules]
        for key in remove:
            del sys.modules[key]
        sys.path[:] = orig_path
        sys.meta_path[:] = orig_meta_path
        sys.path_hooks[:] = orig_path_hooks
        sys.path_importer_cache.clear()
        sys.path_importer_cache.update(orig_path_importer_cache)


@pytest.fixture
def extra_site(tmp_path):
    extra_site_dir = tmp_path / "site"
    yield extra_site_dir


def build(target, structure):
    target.mkdir(exist_ok=True, parents=True)
    for name, content in structure.items():
        path = target / name
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            build(path, content)


def test_redirects(tmp_path):
    project = tmp_path / "project"
    project_files = {
        "mod.py": "val = 42",
        "pkg": {
            "__init__.py": "val = 42",
            "sub.py": "val = 42",
        },
    }
    build(project, project_files)

    r = Redirector("xxx")
    r.redirect(project / "mod.py")
    r.redirect(project / "pkg")

    sitedir = tmp_path / "site"
    sitedir.mkdir()
    for name, content in r.files():
        (sitedir / name).write_text(content, encoding="utf-8")

    with save_import_state():
        site.addsitedir(str(sitedir))

        import mod

        assert mod.val == 42
        import pkg

        assert pkg.val == 42
        import pkg.sub

        assert pkg.sub.val == 42
