import ast
import os
import re
import sys

regex = re.compile(r"^import (spack\.[a-zA-Z0-9_\.]+)$", re.MULTILINE)

for file in sys.argv:
    contents = open(file, "r").read()

    to_remove = []

    for m in regex.finditer(contents):
        if contents.count(m.group(1)) == 1:
            print(file, m.group(0))
            to_remove.append(m.group(0))

    if not to_remove:
        continue

    for imp in to_remove:
        contents = contents.replace(f"{imp}\n", "")

    with open(file, "w") as f:
        f.write(contents)
