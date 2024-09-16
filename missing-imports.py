import ast
import os
import re
import sys

nope = re.compile(r"(from |import |\"|\'|^\s*#.+)spack\.[a-zA-Z0-9_\.]+")
regex = re.compile(r"spack\.[a-zA-Z0-9_\.]+")


def module_part(expr: str):
    parts = expr.split(".")
    while parts:
        f1 = os.path.join("lib", "spack", *parts) + ".py"
        f2 = os.path.join("lib", "spack", *parts, "__init__.py")
        if os.path.exists(f1) or os.path.exists(f2):
            return ".".join(parts)
        parts.pop()
    return None


for file in sys.argv:
    found = set()
    parsed = ast.parse(open(file, "r").read())

    # Clear all strings
    for node in ast.walk(parsed):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            node.value = ""

    contents = ast.unparse(parsed)
    for line in contents.splitlines():
        if nope.search(line):
            continue

        for x in regex.finditer(line):
            module = module_part(x.group(0))
            if not module or module in found:
                continue
            if f"import {module}" not in contents:
                found.add(module)
                print(file, module)

    # insert import module statements after the first line
    if found:

        try:
            for node in parsed.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    first_line = node.lineno
                    break
            else:
                print("skip", file)
        except IndexError:
            print("skip", file)
            continue
        with open(file, "r") as f:
            lines = f.readlines()
        lines.insert(first_line, "\n".join([f"import {x}" for x in found]) + "\n")
        with open(file, "w") as f:
            f.write("".join(lines))
