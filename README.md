How to run this:

1. Install julia: `curl -fsSL https://install.julialang.org | sh`
2. Run `make SPACK_ROOT=/path/to/spack JULIA=/path/to/bin/julia PYTHON=/path/to/bin/python3`

This outputs the minimal set of imports to remove from the codebase (output to stdout and the
file `solution`).

There are also a few helper scripts:
1. `python3 missing-imports.py $(find /path/to/spack/lib/spack/spack -name '*.py')` adds import
   statements to files that are missing them.
2. `python3 redundant-imports.py $(find /path/to/spack/lib/spack/spack -name '*.py')` removes
   redundant import statements from files.