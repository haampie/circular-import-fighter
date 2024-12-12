.PHONY: all clean dependencies

all: solution

JULIA = julia
PYTHON = python3
SPACK_ROOT ?= ~/spack

venv/bin/python3:
	@$(PYTHON) -m venv venv
	@./venv/bin/pip install pydeps

dependencies: Manifest.toml venv/bin/python3

graph.json: venv/bin/python3
	@./venv/bin/python3 -mpydeps --noshow --nodot --show-deps --deps-output=graph.json $(SPACK_ROOT)/lib/spack/spack

graph.txt: graph.json venv/bin/python3 simplify_graph.py
	@./venv/bin/python3 simplify_graph.py

Manifest.toml:
	@$(JULIA) --project=. -e 'using Pkg; Pkg.add(PackageSpec(url="https://github.com/GunnarFarneback/FeedbackArcSets.jl.git", rev="6f0f15d252e7f17d3328babfbaea87b7a7558702")); Pkg.add("Graphs"); Pkg.instantiate()'

solution: graph.txt Manifest.toml solve.jl
	@$(JULIA) --project=. ./solve.jl > $@
	cat $@

clean-graph:
	rm -f graph.json

clean:
	rm -rf graph.json graph.txt Manifest.toml Project.toml solution venv
