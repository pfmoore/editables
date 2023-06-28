import glob
import shutil

import nox

nox.options.sessions = ["lint"]
nox.options.reuse_existing_virtualenvs = True


@nox.session
def tests(session):
    session.install("-r", "tests/requirements.txt")
    session.install(".")

    session.run(
        "pytest",
        "--cov-report",
        "term-missing",
        "--cov",
        "editables",
        "tests",
        *session.posargs,
    )


@nox.session
def lint(session):
    # Run the linters (via pre-commit)
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files", *session.posargs)


@nox.session
def build(session):
    # Check the distribution
    session.install("build", "twine")
    session.run("pyproject-build")
    session.run("twine", "check", *glob.glob("dist/*"))


@nox.session
def docs(session):
    shutil.rmtree("docs/build", ignore_errors=True)
    session.install("-r", "docs/requirements.txt")

    session.run(
        "sphinx-build",
        "-b",
        "html",
        "docs/source",  # source directory
        "docs/build",  # output directory
    )
