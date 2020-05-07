from setuptools import __version__, setup

if int(__version__.split(".")[0]) < 41:
    raise RuntimeError("setuptools >= 41 required to build")

setup(
    use_scm_version={"write_to": "src/editables/version.py", "write_to_template": '__version__ = "{version}"'},
    setup_requires=["setuptools_scm >= 2"],
)
