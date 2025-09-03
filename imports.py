import ast
import sys
import os
import re
from typing import Set, Tuple, List, Dict


class ImportVisitor(ast.NodeVisitor):
    def __init__(self, root: str, current_pkg: str, regex: re.Pattern):
        self.imported: Set[str] = set()
        self.root = root
        self.current_pkg = current_pkg
        self.regex = regex

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
            # Immediately skip if the parent does not satisfy the regex, which saves stat calls.
            if not self.regex.match(module):
                continue
            init_file = os.path.join(
                self.root,
                module.replace(".", os.path.sep),
                alias.name,
                "__init__.py",
            )
            module_file = os.path.join(
                self.root,
                module.replace(".", os.path.sep),
                f"{alias.name}.py",
            )
            # Distinguish between importing a submodule or an attribute.
            if os.path.isfile(init_file) or os.path.isfile(module_file):
                resolved_module = f"{module}.{alias.name}"
            else:
                resolved_module = module

            if self.regex.match(resolved_module):
                self.imported.add(resolved_module)

    def visit_If(self, node):
        # do not recurse into if TYPE_CHECKING blocks
        if isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            return
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # do not recurse into functions
        pass

    def visit_AsyncFunctionDef(self, node):
        # do not recurse into async functions
        pass

    def visit_ClassDef(self, node):
        # do not recurse into classes
        pass


def analyze_imports(path: str, root: str, current_pkg: str, regex: re.Pattern):
    """Parses Python source code and collects only top-level imports.
    The `relative_to` parameter is the package *directory* the source code is relative to.
    """
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    visitor = ImportVisitor(root, current_pkg, regex)
    visitor.visit(tree)
    return visitor.imported


def _is_package_dir(entry: os.DirEntry[str]) -> bool:
    return (
        entry.name.isidentifier()
        and not entry.name == "__pycache__"
        and entry.is_dir(follow_symlinks=False)
    )


def _is_module_file(entry: os.DirEntry[str]) -> bool:
    return entry.is_file(follow_symlinks=False) and entry.name.endswith(".py")


def check_project(root: str, pkg: str, pattern: str):
    root_pkg_dir = os.path.join(root, pkg)
    stack = [root_pkg_dir]
    regex = re.compile(pattern)
    edges_str: List[Tuple[str, str]] = []

    while stack:
        sub_pkg_dir = stack.pop()

        # check if this is a package
        if not os.path.isfile(os.path.join(sub_pkg_dir, "__init__.py")):
            continue

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
                        entry.path, root=root, current_pkg=subpkg, regex=regex
                    ):
                        edges_str.append((current_module, submodule))

    node_to_index: Dict[str, int] = {
        node: idx
        for idx, node in enumerate(sorted(set(x for edge in edges_str for x in edge)))
    }

    print(len(node_to_index))
    for node in node_to_index:
        print(node)
    print(len(edges_str))
    for from_node, to_node in edges_str:
        print(f"{node_to_index[from_node]} {node_to_index[to_node]}")


if __name__ == "__main__":
    check_project(*sys.argv[1:], pkg="spack", pattern=r"spack(?!\.vendor)(?!\.test)")
