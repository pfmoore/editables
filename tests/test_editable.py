import subprocess

import pytest
from virtualenv import cli_run

from editables import build_editable


def build_project(to, structure):
    to.mkdir(exist_ok=True, parents=True)
    for name, content in structure.items():
        path = to / name
        if isinstance(content, str):
            path.write_text(content)
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
    files = [f for f, src in build_editable(str(project))]
    assert files == ["foo.py"]
    files = {f for f, src in build_editable(str(project / "foo"))}
    assert files == {"bar.py", "baz.py"}


@pytest.mark.parametrize(
    "expose,hide", [(None, None), (None, ["foo.bar"]), ("foo", ["foo.bar", "foo.baz"])]
)
def test_hook_vars(project, expose, hide):

    filename, src = next(build_editable(str(project), expose=expose, hide=hide))

    # Remove the line that runs the bootstrap
    src = "\n".join(line for line in src.splitlines() if line != "_bootstrap()")
    global_dict = {"__builtins__": __builtins__}
    exec(src, global_dict)
    assert global_dict["location"] == str(project), str(src)
    assert set(global_dict["excludes"]) == set(hide or []), str(src)


def test_editable_expose_hide(tmp_path, capfd, project):
    # install to a virtual environment
    result = cli_run([str(tmp_path / "venv"), "--without-pip"])
    for name, code in build_editable(str(project), expose=["foo"], hide=["foo.bar"]):
        (result.creator.purelib / name).write_text(code)

    # test it works
    subprocess.check_call([str(result.creator.exe), "-c", "import foo; print(foo)"])
    capfd.readouterr()

    with pytest.raises(subprocess.CalledProcessError):
        subprocess.check_call([str(result.creator.exe), "-c", "import foo.bar"])
    _, err = capfd.readouterr()
    assert "foo.bar is excluded from packaging" in err


def test_editable_hide_none(tmp_path, capfd, project):
    # install to a virtual environment
    result = cli_run([str(tmp_path / "venv"), "--without-pip"])
    for name, code in build_editable(str(project), expose=["foo"]):
        (result.creator.purelib / name).write_text(code)

    # test that both foo and foo.bar are exposed
    subprocess.check_call([str(result.creator.exe), "-c", "import foo; print(foo)"])
    capfd.readouterr()
    subprocess.check_call(
        [str(result.creator.exe), "-c", "import foo.bar; print(foo.bar)"]
    )
    capfd.readouterr()


def test_editable_defaults(tmp_path, capfd, project):
    # install to a virtual environment
    result = cli_run([str(tmp_path / "venv"), "--without-pip"])
    for name, code in build_editable(str(project)):
        (result.creator.purelib / name).write_text(code)

    # test that both foo and foo.bar are exposed
    subprocess.check_call([str(result.creator.exe), "-c", "import foo; print(foo)"])
    capfd.readouterr()
    subprocess.check_call(
        [str(result.creator.exe), "-c", "import foo.bar; print(foo.bar)"]
    )
    capfd.readouterr()
