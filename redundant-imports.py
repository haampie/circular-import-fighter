import ast
import os
import re
import sys

regex = re.compile(r"^import (spack\.[a-zA-Z0-9_\.]+)$", re.MULTILINE)

for file in sys.argv:
    found = set()
    contents = open(file, "r").read()

    for match in regex.finditer(contents):
        if contents.count(match.group(1)) == 1:
            print(file, match.group(0))
