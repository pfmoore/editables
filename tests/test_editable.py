import contextlib
import os
import site
import sys

import pytest

from editables import EditableProject

# Use a project name that is not a valid Python identifier,
# to test that it gets normalised correctly
PROJECT_NAME = "my-project"


def build_project(target, structure):
    target.mkdir(exist_ok=True, parents=True)
    for name, content in structure.items():
        path = target / name
        if isinstance(content, str):
            # If the name contains slashes, create any
            # required parent directories
            path.parent.mkdir(exist_ok=True, parents=True)
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
            "__init__.py": "from .baz import num; num = 1; print('foo');",
            "bar": {"__init__.py": "num = 2; print('foo.bar')"},
            "baz.py": "num = 3; print('foo.baz')",
        },
        "qux.py": "num = 4; print('module')",
    }
    build_project(project, structure)
    yield project


def test_not_toplevel(tmp_path, project):
    p = EditableProject(PROJECT_NAME, project)
    p.map("foo.bar", "foo/bar")
    p.map("foo.baz", "foo/baz.py")
    structure = {name: content for name, content in p.files()}
    print(structure.keys())
    site_packages = tmp_path / "site-packages"
    build_project(site_packages, structure)
    for _ in range(3):
        with import_state(extra_site=site_packages):
            import foo.bar
            import foo.baz

            assert not hasattr(foo, "num")
            assert foo.bar.num == 2
            assert foo.baz.num == 3


def test_simple_pth(tmp_path, project):
    (project / "__pycache__").mkdir()
    if hasattr(os, "mkfifo"):
        os.mkfifo(project / "neither_a_file_nor_a_directory")
    p = EditableProject(PROJECT_NAME, project)
    p.add_to_path(".")
    structure = {name: content for name, content in p.files()}
    print(structure.keys())
    site_packages = tmp_path / "site-packages"
    build_project(site_packages, structure)
    for _ in range(3):
        with import_state(extra_site=site_packages):
            import foo
            import qux

            assert foo.num == 1
            assert qux.num == 4


def test_make_project(project, tmp_path):
    p = EditableProject(PROJECT_NAME, project)
    p.map("foo", "foo")
    structure = {name: content for name, content in p.files()}
    site_packages = tmp_path / "site-packages"
    build_project(site_packages, structure)
    for _ in range(3):
        with import_state(extra_site=site_packages):
            import foo

            assert foo.num == 1


def test_subpackage_pth(tmp_path, project):
    p = EditableProject(PROJECT_NAME, project)
    p.add_to_subpackage(".a.b", ".")
    structure = {name: content for name, content in p.files()}
    site_packages = tmp_path / "site-packages"
    build_project(site_packages, structure)
    for _ in range(3):
        with import_state(extra_site=site_packages):
            import a.b.foo
            import a.b.qux

            assert a.b.foo.num == 1
            assert a.b.qux.num == 4
