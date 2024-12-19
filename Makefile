.PHONY: all clean dependencies

JULIA = julia
PYTHON = python3
SPACK_ROOT ?= ~/spack
SUFFIX =

all: solution$(SUFFIX)

venv/bin/python3:
	@$(PYTHON) -m venv venv
	@./venv/bin/pip install pydeps

dependencies: Manifest.toml venv/bin/python3

graph$(SUFFIX).json: venv/bin/python3
	./venv/bin/python3 -mpydeps --noshow --nodot --show-deps --deps-output=$@ $(SPACK_ROOT)/lib/spack/spack

graph$(SUFFIX).txt: graph$(SUFFIX).json venv/bin/python3 simplify_graph.py
	@./venv/bin/python3 simplify_graph.py $< $@

Manifest.toml:
	@$(JULIA) --project=. -e 'using Pkg; Pkg.add(PackageSpec(url="https://github.com/GunnarFarneback/FeedbackArcSets.jl.git", rev="6f0f15d252e7f17d3328babfbaea87b7a7558702")); Pkg.add("Graphs"); Pkg.instantiate()'

solution$(SUFFIX): graph$(SUFFIX).txt Manifest.toml solve.jl
	@$(JULIA) --project=. ./solve.jl $< $@
	@cat $@

clean-graph:
	rm -f $(wildcard graph*.json graph*.txt)

clean:
	rm -rf $(wildcard graph*.json graph*.txt solution*) Manifest.toml Project.toml venv
