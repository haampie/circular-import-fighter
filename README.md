How to run this:

1. Install julia: `curl -fsSL https://install.julialang.org | sh`
2. Run
   ```console
   make SPACK_ROOT=/path/to/spack JULIA=/path/to/bin/julia
   ```

This outputs the minimal set of imports to remove from the codebase (output to
stdout and the file `solution`).

