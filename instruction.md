The C project in `/app/project` builds a small command-line tool, `logstat`, which reads log lines on stdin and prints a count per log level. Running `make` builds two programs:

- `bin/logstat`: the release build.
- `bin/logstat-debug`: the same program compiled with `-DDEBUG`, which also prints one `debug:` line to stderr for every record it parses.

The build is broken. CI runs `make -j16` and fails at random. Developers also report that after editing a header the programs sometimes print wrong counts until they run `make clean`, and that the release binary sometimes prints debug lines.

Fix the build so that, starting from `make clean` and run from `/app/project`:

1. `make` with any `-j` level always succeeds and builds both programs correctly. `bin/logstat` must never contain debug code.
2. Running `make` again when nothing has changed does nothing: no file in the project is rewritten.
3. After a change to any `.c` file, any header, or `VERSION`, a single `make` brings both programs fully up to date and rebuilds only what is affected. An object file must be recompiled if, and only if, its source file or a header it includes (directly or indirectly) has changed. The library code in `lib/` is compiled once and linked into both programs; the files in `src/` are compiled once per program.
4. `gen/version.h` is generated from `VERSION` by `scripts/genversion.sh`, and both programs' `--version` output must always match the current `VERSION` file.
5. `make clean` removes all build outputs.

Rules:

- Change only the build files: Makefiles (you may add, remove or restructure them, including `.mk` files). Do not modify any `.c` or `.h` file, `scripts/genversion.sh`, `VERSION` or `sample.log`.
- Do not disable or limit parallelism: no `.NOTPARALLEL`, and do not set or override `MAKEFLAGS`.
- Use the GNU Make and GCC already installed.

`sample.log` is a small example input: `./bin/logstat < sample.log`.
