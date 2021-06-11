import contextlib
import os
import site
import sys
from pathlib import Path

import pytest

from editables import EditableException, EditableProject


def build_project(target, structure):
    target.mkdir(exist_ok=True, parents=True)
    for name, content in structure.items():
        path = target / name
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            build_project(path, content)


# to test in-process:
#   Put stuff in somedir
#   sys.path.append("somedir")
#   site.addsitedir("somedir")
#   Check stuff is visible
@contextlib.contextmanager
def import_state(extra_site=None):
    extra_site = os.fspath(extra_site)
    orig_modules = set(sys.modules.keys())
    orig_path = list(sys.path)
    orig_meta_path = list(sys.meta_path)
    orig_path_hooks = list(sys.path_hooks)
    orig_path_importer_cache = sys.path_importer_cache
    if extra_site:
        sys.path.append(extra_site)
        site.addsitedir(extra_site)
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
def project(tmp_path):
    project = tmp_path / "project"
    structure = {
        "foo": {
            "__init__.py": "print('foo')",
            "bar": {"__init__.py": "print('foo.bar')"},
            "baz": {"__init__.py": "print('foo.baz')"},
        }
    }
    build_project(project, structure)
    yield project


def test_nonexistent_module(project):
    p = EditableProject("my-project", project)
    with pytest.raises(EditableException):
        p.map("foo", "xxx")


def test_not_toplevel(project):
    p = EditableProject("my-project", project)
    with pytest.raises(EditableException):
        p.map("foo.bar", "foo/bar")


def test_dependencies(project):
    p = EditableProject("my-project", project)
    assert len(p.dependencies()) == 0
    p.map("foo", "foo")
    assert len(p.dependencies()) == 1


def test_simple_pth(tmp_path, project):
    p = EditableProject("my-project", project)
    p.add_to_path(".")
    structure = {name: content for name, content in p.files()}
    site_packages = tmp_path / "site-packages"
    build_project(site_packages, structure)
    with import_state(extra_site=site_packages):
        import foo

        assert Path(foo.__file__) == project / "foo/__init__.py"


def test_make_project(project, tmp_path):
    p = EditableProject("my-project", project)
    p.map("foo", "foo")
    structure = {name: content for name, content in p.files()}
    site_packages = tmp_path / "site-packages"
    build_project(site_packages, structure)
    with import_state(extra_site=site_packages):
        import foo

        assert Path(foo.__file__) == project / "foo/__init__.py"
