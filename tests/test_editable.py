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


def test_editable_expose_hide(tmp_path, capfd):
    # create example
    project = tmp_path / "project"
    structure = {"foo": {"__init__.py": "print('foo')", "bar": {"__init__.py": "print('foo.bar')"}}}
    build_project(project, structure)

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
