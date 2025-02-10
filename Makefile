.PHONY: all clean dependencies

JULIA = julia
PYTHON = python3
SPACK_ROOT ?= ~/spack

all: solution

venv/bin/python3:
	@$(PYTHON) -m venv venv
	@./venv/bin/pip install pydeps

dependencies: Manifest.toml venv/bin/python3

graph-%.json: venv/bin/python3
	./venv/bin/python3 -mpydeps --noshow --nodot --show-deps --deps-output=$@ $(word $*, $(SPACK_ROOT))/lib/spack/spack

graph-%.txt: graph-%.json venv/bin/python3 simplify_graph.py
	@./venv/bin/python3 simplify_graph.py $< $@

Manifest.toml:
	@$(JULIA) --project=. -e 'using Pkg; Pkg.add(PackageSpec(url="https://github.com/GunnarFarneback/FeedbackArcSets.jl.git", rev="0b79f19864275e761acbc877e9d0e180d6e8cd45")); Pkg.add("Graphs"); Pkg.instantiate()'

solution: graph-1.txt Manifest.toml solve.jl
	@$(JULIA) --project=. ./solve.jl $< $@
	@cat $@

clean-graph:
	rm -f $(wildcard graph*.json graph*.txt)

compare: graph-1.txt graph-2.txt Manifest.toml compare.jl
	@$(JULIA) --project=. --color=yes ./compare.jl graph-1.txt graph-2.txt

clean:
	rm -rf $(wildcard graph*.json graph*.txt solution*) Manifest.toml Project.toml venv
