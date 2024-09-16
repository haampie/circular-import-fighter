#!/usr/bin/env python3

from collections import defaultdict

delete = [
    ("spack.bootstrap.core", "spack.binary_distribution"),
    ("spack.build_environment", "spack.build_systems.cmake"),
    ("spack.builder", "spack.build_environment"),
    ("spack.compiler", "spack.spec"),
    ("spack.compiler", "spack.util.libc"),
    ("spack.config", "spack.environment.environment"),
    ("spack.config", "spack.schema.ci"),
    ("spack.config", "spack.schema.env"),
    ("spack.config", "spack.util.web"),
    ("spack.directives", "spack.package_base"),
    ("spack.environment", "spack.environment.environment"),
    ("spack.fetch_strategy", "spack.oci.opener"),
    ("spack.fetch_strategy", "spack.version.git_ref_lookup"),
    ("spack.install_test", "spack.build_environment"),
    ("spack.installer", "spack.build_environment"),
    ("spack.installer", "spack.package_base"),
    ("spack.modules.common", "spack.build_environment"),
    ("spack.parser", "spack.spec"),
    ("spack.platforms", "spack.config"),
    ("spack.provider_index", "spack.spec"),
    ("spack.repo", "spack.package_base"),
    ("spack.repo", "spack.patch"),
    ("spack.repo", "spack.spec"),
    ("spack.spec", "spack.compilers"),
    ("spack.spec", "spack.solver.asp"),
    ("spack.spec", "spack.store"),
    ("spack.target", "spack.compilers"),
    ("spack.target", "spack.spec"),
    ("spack.traverse", "spack.spec"),
    ("spack.user_environment", "spack.build_environment"),
    ("spack.util.cpus", "spack.config"),
    ("spack.util.package_hash", "spack.package_base"),
    ("spack.util.path", "spack.spec"),
    ("spack.util.s3", "spack.mirror"),
]

with open("graph.txt", "r") as f:
    nnodes = int(f.readline())

    node_names = []

    for i in range(nnodes):
        node_names.append(f.readline().strip())

    nedges = int(f.readline())
    graph = defaultdict(list)

    for i in range(nedges):
        parent, child = (int(x) for x in f.readline().strip().split(" "))
        if parent == child:
            print(f"skipping {node_names[parent]} self cycle")
            continue
        graph[node_names[parent]].append(node_names[child])


for parent, child in sorted(delete):
    try:
        graph[parent].remove(child)
    except ValueError:
        print(f"edge {parent} -> {child} not found")
        continue

def dfs(graph, node, visited):
    if visited[node] == 2:
        return True

    elif visited[node] == 1:  # cycle
        return False

    visited[node] = 1

    if node in graph:
        for child in graph[node]:
            if not dfs(graph, child, visited):
                print(node, child)
                return False

    visited[node] = 2

    return True

visited = {name: 0 for name in node_names}

for node in graph:
    if visited[node] != 2 and not dfs(graph, node, visited):
        print(f"cycle detected: {i}")
        exit(1)
