How to run this:

1. Install julia: `curl -fsSL https://install.julialang.org | sh`
2. Run `make SPACK_ROOT=/path/to/spack` (default is `SPACK_ROOT=~/spack`)
3. Run `make clean-graph && make` after code changes to Spack

This outputs the minimal set of imports to remove from the codebase (output to
stdout and the file `solution`).

