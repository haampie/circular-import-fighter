#!/usr/bin/env python3

import ast
import os
import re
from typing import Set, Tuple
import functools
import argparse
from typing import IO
import sys


@functools.lru_cache(maxsize=None)
def resolve_module(root: str, module: str, attr: str) -> str:
    """Resolve ``from foo import bar`` to either ``foo.bar`` or ``foo``, depending on whether bar
    is a submodule or an attribute."""
    init_file = os.path.join(
        root,
        module.replace(".", os.path.sep),
        attr,
        "__init__.py",
    )
    module_file = os.path.join(
        root,
        module.replace(".", os.path.sep),
        f"{attr}.py",
    )
    if os.path.isfile(init_file) or os.path.isfile(module_file):
        return f"{module}.{attr}"
    return module


class ImportVisitor(ast.NodeVisitor):
    def __init__(self, root: str, current_pkg: str, regex: re.Pattern, inline: bool):
        self.imported: Set[str] = set()
        self.root = root
        self.current_pkg = current_pkg
        self.regex = regex
        self.inline = inline

    def visit_Import(self, node):
        # import statements are always absolute
        for alias in node.names:
            if self.regex.match(alias.name):
                self.imported.add(alias.name)

    def visit_ImportFrom(self, node):
        # import from can be relative or absolute, and the alias can be a submodule or attribute
        if node.level == 0:
            module = self.current_pkg if node.module is None else node.module
        elif node.level > 0:
            parts = self.current_pkg.split(".")
            parts = parts[0 : len(parts) - node.level + 1]
            module = ".".join(parts)

            if node.module is not None:
                module = f"{module}.{node.module}"
        else:
            assert False, "Should not be here"

        for alias in node.names:
            resolved_module = resolve_module(self.root, module, alias.name)
            if self.regex.match(resolved_module):
                self.imported.add(resolved_module)

    def visit_If(self, node):
        # do not recurse into if TYPE_CHECKING blocks
        if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            return
        elif isinstance(node.test, ast.Attribute) and node.test.attr == "TYPE_CHECKING":
            return
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if self.inline:
            self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        if self.inline:
            self.generic_visit(node)

    def visit_ClassDef(self, node):
        if self.inline:
            self.generic_visit(node)


def analyze_imports(
    path: str, root: str, current_pkg: str, regex: re.Pattern, inline: bool
) -> Set[str]:
    """Parses Python source code and collects only top-level imports.

    Args:
        path: Path to the Python file to analyze
        root: Root directory of the project
        current_pkg: Package namespace of the module being analyzed
        regex: Pattern to filter which imports to include
        inline: Whether to include inline imports (inside functions, classes, etc.)
    """
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    visitor = ImportVisitor(root, current_pkg, regex, inline)
    visitor.visit(tree)
    return visitor.imported


def _is_package_dir(entry: os.DirEntry[str]) -> bool:
    return (
        entry.name.isidentifier()
        and not entry.name == "__pycache__"
        and entry.is_dir(follow_symlinks=False)
        and os.path.isfile(os.path.join(entry.path, "__init__.py"))
    )


def _is_module_file(entry: os.DirEntry[str]) -> bool:
    return entry.is_file(follow_symlinks=False) and entry.name.endswith(".py")


def check_project(root: str, pkg: str, pattern: str, inline: bool, output: IO[str]):
    """Analyze a Python project for import relationships between modules.

    Args:
        root: Root directory of the project
        pkg: Name of the package to analyze (e.g. "spack")
        pattern: Regex pattern to filter which modules to include
        inline: Whether to include inline imports (inside functions, classes, etc.)
        output: Output stream to write results to

    Prints:
        The Python module graph: first the number of nodes, then the nodes (one per line),
        then the number of edges, then the edges, one per line as "from to", by index, starting
        from 0.
    """
    root_pkg_dir = os.path.join(root, pkg)
    stack = [root_pkg_dir]
    regex = re.compile(pattern)
    edges: Set[Tuple[str, str]] = set()

    while stack:
        sub_pkg_dir = stack.pop()
        subpkg = os.path.relpath(sub_pkg_dir, root).replace(os.sep, ".")

        if not regex.search(subpkg):
            continue

        with os.scandir(sub_pkg_dir) as it:
            for entry in it:
                if _is_package_dir(entry):
                    stack.append(entry.path)
                elif _is_module_file(entry):
                    if entry.name == "__init__.py":
                        current_module = subpkg
                    else:
                        current_module = f"{subpkg}.{entry.name[:-3]}"
                    for submodule in analyze_imports(
                        entry.path,
                        root=root,
                        current_pkg=subpkg,
                        regex=regex,
                        inline=inline,
                    ):
                        edges.add((current_module, submodule))

    node_to_index = {
        node: idx
        for idx, node in enumerate(sorted(set(x for edge in edges for x in edge)))
    }

    adjacency_list = {node: set() for node in node_to_index}
    for src, dst in edges:
        adjacency_list[src].add(dst)

    # There are cases where a package foo re-exports from submodules, and those submodules do
    # many additional imports, e.g. x imports x.y imports {foo, bar, baz}. A simple solution for
    # the purpose of cycle elimination is to delete the edge x -> x.y, since that prunes the
    # {foo, bar, baz} dependencies. However, that's practically infeasible since with re-exports
    # the point is to expose the submodules as part of the parent module's API. To handle this,
    # we propagate all child edges to the parent, so x -> {foo, bar, baz} too.
    for src, dst in edges:
        if dst.startswith(f"{src}."):
            adjacency_list[src].update(adjacency_list[dst])

    total_edges = sum(len(dsts) for dsts in adjacency_list.values())

    print(len(node_to_index), file=output)
    for node in node_to_index:
        print(node, file=output)
    print(total_edges, file=output)
    for parent, children in adjacency_list.items():
        for child in children:
            print(f"{node_to_index[parent]} {node_to_index[child]}", file=output)


def main():
    """Main function to parse arguments and run the analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze Python project imports to find cycles"
    )
    parser.add_argument(
        "root", help="PYTHONPATH root of the project: e.g. ~/spack/lib/spack"
    )
    parser.add_argument(
        "--pkg",
        default="spack",
        help="The name of the package to analyze (default: spack)",
    )
    parser.add_argument(
        "--pattern",
        default=r"spack(?!\.vendor)(?!\.test)",
        help="The regex pattern to filter modules",
    )
    parser.add_argument(
        "--inline",
        action="store_true",
        help="Include inline imports",
    )
    parser.add_argument(
        "--output", "-o", help="Output file (default: stdout)", default=None
    )
    args = parser.parse_args()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            check_project(args.root, args.pkg, args.pattern, args.inline, f)
    else:
        check_project(args.root, args.pkg, args.pattern, args.inline, sys.stdout)


if __name__ == "__main__":
    main()
