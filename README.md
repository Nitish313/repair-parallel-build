# repair-parallel-build

A Terminal-Bench style task (Harbor format) about debugging a broken build system.

The agent gets a small C project (`logstat`, a log-level counter) whose recursive Makefiles look fine on a normal `make` but are wrong in four ways. It has to fix only the build files so that parallel, incremental and no-op builds are all exactly right.

## Layout

| Path | What it is |
|---|---|
| `instruction.md` | What the agent sees |
| `environment/` | Dockerfile and the broken project copied to `/app/project` |
| `solution/` | Reference fix (one non-recursive Makefile) and `solve.sh` |
| `tests/` | Hidden verifier (`check.py`), run by `test.sh`; writes `reward.txt` (1 or 0) |

## The bugs

1. **Generated header race.** `gen/version.h` is made by a `.PHONY` target, but nothing compiled depends on it, so under `make -j` `main.c` can compile before the header exists. It is also rewritten on every run.
2. **No header dependencies.** Neither Makefile tracks `#include`s, so after changing a header the old objects are reused. If a struct layout changes, the library and the program disagree on field offsets and print wrong counts.
3. **Release and debug variants share object files.** The debug rule recompiles `src/*.o` with `-DDEBUG` in place. On the next `make` the release binary is relinked from debug objects, and under `-j` the two variants race on the same files.
4. **Recursive make that never re-enters `lib/`.** `lib/libcore.a` has a rule with no prerequisites, so changes to library sources are never rebuilt once the archive exists.

## Why it is hard

- On a fresh clone `make` succeeds and the output looks right. The bugs show up only under `-j`, after an edit, or on a second run.
- Each bug has an easy fix that breaks another requirement, and the verifier checks for each one:
  - **Always clean, or force everything:** fails the no-op check, which snapshots every file's mtime.
  - **Making `gen/version.h` a normal prerequisite of all objects:** builds correctly but recompiles `report.c` on a version bump. The verifier counts recompiled objects per change, and only an order-only prerequisite plus compiler-generated `.d` files gives the exact count.
  - **`.NOTPARALLEL`, `-j1` or `MAKEFLAGS` tricks:** banned by the instruction and checked.
  - **Editing the C code to avoid the version macro:** all sources are hash-checked.
- The verifier makes the header generator slow (`sleep 1`), so the race shows up every time instead of by luck.
- It also changes a struct layout and checks the output, so stale objects cause a real failure, not just a timestamp mismatch.

## What the verifier checks

- **Protected files:** they are unchanged, and no Makefile disables parallelism.
- **Clean builds:** three clean `make -j16` builds with the slow generator, plus one `-j1` build, each giving correct output from both programs. The release build must print no debug lines, and `--version` must match `VERSION`.
- **No-op builds:** `make` with nothing changed rewrites no file.
- **Exact rebuilds:** after touching each header and source file, the number of recompiled objects is exact:

  | File touched | Objects recompiled |
  |---|---|
  | `record.h` | 6 |
  | `stats.h` | 5 |
  | `parse_internal.h` | 1 |
  | `parse.c` | 1 |
  | `report.c` | 2 |
  | `VERSION` changed | 2 |

  Both programs must be relinked each time.
- **Struct layout change:** the programs still give correct output after a struct layout change.

## Results so far

- `harbor run -a oracle`: reward 1.0
- `harbor run -a nop`: reward 0.0 (race, no-op, stale header and debug-leak failures)
- Three common half-fixes each score 0 for the expected reason:
  - version header as a normal prerequisite;
  - clean before every build;
  - no `-MMD`.

It has not been run against frontier models, so its difficulty for them is not measured.
