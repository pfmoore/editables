# Very hacky script to bump the version when cutting a new release.
#
# This does the following:
#
# 1. Edit the version number in the 3 places in the code it's specified
# 2. Commit the change to git
# 3. Tag the commit with the version
#
# Note - this assumes that you will *immediately* release the new version,
# if you make changes before doing so, the tag will not match the release.

import re
import subprocess
import sys
from pathlib import Path

new_version = sys.argv[1]

files = [
    ("src/editables/__init__.py", r'^__version__ = "(\d+\.\d+)"$'),
    ("pyproject.toml", r'^version = "(\d+\.\d+)"$'),
    ("docs/source/conf.py", r'^release = "(\d+\.\d+)"$'),
]


def repl(m):
    # Replace group 1 with new_version
    return (
        m.group(0)[: m.start(1) - m.start(0)]
        + new_version
        + m.group(0)[m.end(1) - m.start(0) :]
    )


for file, regex in files:
    file = Path(file)
    content = file.read_text(encoding="utf-8")
    new_content = re.sub(regex, repl, content, flags=re.MULTILINE)
    file.write_text(new_content, encoding="utf-8")

subprocess.run(["git", "add"] + [f for f, re in files])
subprocess.run(["git", "commit", "-m", f"Bump version to {new_version}"])
subprocess.run(["git", "tag", new_version])
