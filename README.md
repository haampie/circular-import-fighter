How to run this:

1. Install julia: `curl -fsSL https://install.julialang.org | sh`
2. Run `make` (you may need to pass/export `SPACK_ROOT=/path/to/spack`)
3. Run `make clean-graph && make` to reflect code changes in Spack

This outputs the minimal set of imports to remove from the codebase (output to
stdout and the file `solution`).

