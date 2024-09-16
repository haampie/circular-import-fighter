#!/usr/bin/env python3

import json
import copy
import os

if not os.path.exists("graph.json"):
    print(
        "Please run `pydeps --noshow --nodot --show-deps "
        "--deps-output=graph.json /path/to/spack/lib/spack/spack`"
    )
    exit(1)


def fixup_edges(graph):
    for data in graph.values():
        data["children"] = [name for name in data["children"] if name in graph]
        data["parents"] = [name for name in data["parents"] if name in graph]


raw_graph = json.load(open("graph.json"))

# remove nodes that do not match `spack.*`
pruned_graph = {
    node: {"children": info.get("imports", []), "parents": info.get("imported_by", [])}
    for node, info in raw_graph.items()
    if node.startswith("spack.")
}

# remove edges to nodes that are not in the graph
fixup_edges(pruned_graph)

aliases = {
    "spack.environment.environment": "spack.environment"
}

for old, new in aliases.items():
    item = pruned_graph.pop(old)

    # make children of old children of new

    for child in item["children"]:
        if child != new:
            pruned_graph[new]["children"].append(child)

    for parent in item["parents"]:
        if parent != new:
            pruned_graph[new]["parents"].append(parent)

    # rewire edges
    for item in pruned_graph.values():
        if old in item["children"]:
            item["children"].remove(old)
            item["children"].append(new)
        if old in item["parents"]:
            item["parents"].remove(old)
            item["parents"].append(new)

# delete dupes
for item in pruned_graph.values():
    item["children"] = sorted(set(item["children"]))
    item["parents"] = sorted(set(item["parents"]))

nodes = sorted(pruned_graph.keys())
with open("graph.txt", "w") as f:
    print(len(nodes), file=f)
    for node in nodes:
        print(node, file=f)
    print(sum(len(edges["children"]) for edges in pruned_graph.values()), file=f)
    for parent, edges in pruned_graph.items():
        for child in edges["children"]:
            print(f"{nodes.index(parent)} {nodes.index(child)}", file=f)