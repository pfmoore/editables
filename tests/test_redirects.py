import contextlib
import sys

from editables.redirector import RedirectingFinder as F


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
        # HACK
        F._redirections = {}


def build(target, structure):
    target.mkdir(exist_ok=True, parents=True)
    for name, content in structure.items():
        path = target / name
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            build(path, content)


def test_double_install():
    with save_import_state():
        old_len = len(sys.meta_path)
        F.install()
        F.install()
        assert len(sys.meta_path) == old_len + 1


def test_toplevel_only():
    assert F.find_spec("foo.bar") is None


def test_no_path():
    assert F.find_spec("foo", path=[]) is None


def test_no_map_returns_none():
    assert F.find_spec("foo") is None


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

    with save_import_state():
        F.install()
        F.map_module("mod", project / "mod.py")
        F.map_module("pkg", project / "pkg/__init__.py")

        import mod

        assert mod.val == 42
        import pkg

        assert pkg.val == 42
        import pkg.sub

        assert pkg.sub.val == 42


def test_namespaces(tmp_path):
    project1 = tmp_path / "project1"
    project1_files = {
        "ns": {
            "foo.py": "val = 1",
            "bar.py": "val = 1",
        },
    }
    build(project1, project1_files)

    project2 = tmp_path / "project2"
    project2_files = {
        "ns": {
            "bar.py": "val = 2",
            "baz.py": "val = 2",
            "boop": {"__init__.py": "val = 2"},
        },
    }
    build(project2, project2_files)

    with save_import_state():
        F.install()
        F.add_namespace_path("ns", project1 / "ns")
        F.add_namespace_path("ns", project2 / "ns")

        import ns.foo

        assert ns.foo.val == 1
        import ns.bar

        assert ns.bar.val == 1
        import ns.baz

        assert ns.baz.val == 2
        import ns.boop

        assert ns.boop.val == 2
