import subprocess

import pytest
import virtualenv

from editables import build_editable


def make_venv(name):
    return virtualenv.cli_run([str(name), "--without-pip"])


def run(*args):
    return subprocess.run(
        [str(a) for a in args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        universal_newlines=True,
    )


def build_project(target, structure):
    target.mkdir(exist_ok=True, parents=True)
    for name, content in structure.items():
        path = target / name
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            build_project(path, content)


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


def test_returns_right_files(project):
    files = [f for f, src in build_editable(project)]
    assert files == ["foo.py"]
    files = {f for f, src in build_editable(project / "foo")}
    assert files == {"bar.py", "baz.py"}


@pytest.mark.parametrize(
    "expose,hide", [(None, None), (None, ["foo.bar"]), ("foo", ["foo.bar", "foo.baz"])]
)
def test_hook_vars(project, expose, hide):

    filename, src = next(build_editable(project, expose=expose, hide=hide))

    # Remove the line that runs the bootstrap
    src = "\n".join(line for line in src.splitlines() if line != "_bootstrap()")
    global_dict = {"__builtins__": __builtins__}
    exec(src, global_dict)
    assert global_dict["location"] == str(project), str(src)
    assert set(global_dict["excludes"]) == set(hide or []), str(src)


def test_editable_expose_hide(tmp_path, project):
    # install to a virtual environment
    result = make_venv(tmp_path / "venv")
    for name, code in build_editable(project, expose=["foo"], hide=["foo.bar"]):
        (result.creator.purelib / name).write_text(code, encoding="utf-8")

    # test it works
    run(result.creator.exe, "-c", "import foo; print(foo)")
    with pytest.raises(subprocess.CalledProcessError):
        ret = run(result.creator.exe, "-c", "import foo.bar")
        assert "foo.bar is excluded from packaging" in ret.stderr


def test_editable_hide_none(tmp_path, project):
    # install to a virtual environment
    result = make_venv(tmp_path / "venv")
    for name, code in build_editable(project, expose=["foo"]):
        (result.creator.purelib / name).write_text(code)

    # test that both foo and foo.bar are exposed
    run(result.creator.exe, "-c", "import foo; print(foo)")
    run(result.creator.exe, "-c", "import foo.bar; print(foo.bar)")


def test_editable_defaults(tmp_path, project):
    # install to a virtual environment
    result = make_venv(tmp_path / "venv")
    for name, code in build_editable(project):
        (result.creator.purelib / name).write_text(code)

    # test that both foo and foo.bar are exposed
    run(result.creator.exe, "-c", "import foo; print(foo)")
    run(result.creator.exe, "-c", "import foo.bar; print(foo.bar)")
