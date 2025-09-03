.PHONY: all clean dependencies

JULIA = julia
PYTHON = python3
IMPORTS_FLAGS =
SPACK_ROOT ?= ~/spack
all: solution

dependencies: Manifest.toml

graph-%.txt: imports.py
	@$(PYTHON) imports.py $(IMPORTS_FLAGS) --output=$@ $(word $*, $(SPACK_ROOT))/lib/spack

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
	rm -rf $(wildcard graph*.txt solution*) Manifest.toml Project.toml venv
