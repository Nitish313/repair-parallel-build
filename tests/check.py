"""Hidden verifier for repair-parallel-build.

Every scenario runs on a fresh copy of /app/project, so the agent's own build
outputs never matter. Reward is 1 only if every check passes.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time

PROJECT = "/app/project"
REWARD = "/logs/verifier/reward.txt"

# The C sources, headers, generator and data must stay exactly as shipped.
PROTECTED = {
    "include/record.h": "e5b0bff4d07db6b868e301b54f9d85ab098c57e543ab0732ffb7ec0db95faa8e",
    "include/stats.h": "268c9d2f2ee8bceea740742e01f18a3f7380d65ae31dd5885ac99723e71e8647",
    "lib/parse.c": "88cb914b01f2f34d869e56b1b1ada79f47d4f1d09c5db6c38339db68e07c4519",
    "lib/stats.c": "9367e65aaf84ebdaa9c7d78ef044d6ef3ced9f34bf58b8e8a617a148d6d4a70f",
    "lib/parse_internal.h": "6444ff1ec983fb4fb8c458566cc36b9a1b3068a42fee42a92ce9fa51ff50cbe3",
    "src/main.c": "c5ed4bdc35207314cd33fc8bceba816e29e89a03d2c107dc541393f74427322e",
    "src/report.c": "74af4780f91a8f4d2e6e8dfa7bbab86ca995667767e33995e235e4f40416c983",
    "scripts/genversion.sh": "4c8920514718fd7b436d6313eebc5155bcdbbdb3ad67559415b75e451f72a414",
    "VERSION": "b99b4c7cdf236f59bc9f65d963deaecae3b16a7dad87939cacb9057f7664daee",
    "sample.log": "05fe3a68768b4722504ac69e45f24c1c9e9e7bd9a68811c5298d0cd0cdbd229a",
}

# Objects that must be recompiled when each input changes. The library is built once;
# src/*.c is built twice (release and debug). Counted, so object naming is free.
EXPECTED_RECOMPILES = {
    "include/record.h": 6,       # parse, stats, main x2, report x2
    "include/stats.h": 5,        # stats, main x2, report x2
    "lib/parse_internal.h": 1,   # parse
    "lib/parse.c": 1,
    "src/report.c": 2,
}

LOG = """INFO alpha
WARN beta
   ERROR gamma with leading spaces

INFO delta
TRACE epsilon
ERROR zeta
INFO eta
"""

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)
        print("FAIL:", msg)
    return cond


def expected_report(text):
    counts = {"INFO": 0, "WARN": 0, "ERROR": 0, "UNKNOWN": 0}
    lines = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        word = line.split()[0]
        counts[word if word in counts else "UNKNOWN"] += 1
        lines += 1
    return "".join(f"{k} {v}\n" for k, v in counts.items()) + f"total {lines}\n", lines


def run(cmd, cwd, timeout=300, stdin=None):
    return subprocess.run(cmd, cwd=cwd, input=stdin, capture_output=True, text=True,
                          timeout=timeout)


def make(cwd, jobs=16):
    return run(["make", f"-j{jobs}"], cwd)


def fresh_copy(slow_generator=False):
    d = tempfile.mkdtemp(prefix="work-")
    shutil.copytree(PROJECT, d, dirs_exist_ok=True, symlinks=True)
    r = run(["make", "clean"], d)
    check(r.returncode == 0, f"'make clean' failed: {r.stderr[-400:]}")
    if slow_generator:
        # A slow header generator exposes any compile that does not wait for gen/version.h.
        real = os.path.join(d, "scripts", ".genversion-real.sh")
        shutil.copy2(os.path.join(d, "scripts", "genversion.sh"), real)
        with open(os.path.join(d, "scripts", "genversion.sh"), "w") as f:
            f.write('#!/bin/sh\nsleep 1\nexec sh "$(dirname "$0")/.genversion-real.sh" "$@"\n')
    return d


def snapshot(d):
    out = {}
    for root, dirs, files in os.walk(d):
        for name in files:
            p = os.path.join(root, name)
            st = os.lstat(p)
            out[os.path.relpath(p, d)] = (st.st_mtime_ns, st.st_size)
    return out


def changed(before, after, suffix=None):
    keys = set(before) | set(after)
    return sorted(k for k in keys if before.get(k) != after.get(k)
                  and (suffix is None or k.endswith(suffix)))


def touch(path):
    time.sleep(0.05)
    now = time.time()
    os.utime(path, (now, now))


def check_binaries(d, label, version="1.4.2"):
    want, nlines = expected_report(LOG)
    rel = run(["./bin/logstat"], d, stdin=LOG, timeout=20)
    check(rel.returncode == 0 and rel.stdout == want,
          f"{label}: bin/logstat output wrong: {rel.stdout!r}")
    check("debug:" not in rel.stderr, f"{label}: release binary prints debug output")
    dbg = run(["./bin/logstat-debug"], d, stdin=LOG, timeout=20)
    check(dbg.returncode == 0 and dbg.stdout == want,
          f"{label}: bin/logstat-debug output wrong: {dbg.stdout!r}")
    check(dbg.stderr.count("debug:") == nlines,
          f"{label}: debug binary should print {nlines} debug lines")
    for b in ("bin/logstat", "bin/logstat-debug"):
        v = run([f"./{b}", "--version"], d, timeout=20)
        check(v.stdout.strip() == f"logstat {version}", f"{label}: {b} --version gave {v.stdout!r}")


def check_noop(d, label):
    before = snapshot(d)
    r = make(d)
    check(r.returncode == 0, f"{label}: no-op make failed")
    check(changed(before, snapshot(d)) == [], f"{label}: up-to-date make changed files: "
          f"{changed(before, snapshot(d))[:6]}")


def test_static():
    for rel, digest in PROTECTED.items():
        p = os.path.join(PROJECT, rel)
        ok = os.path.isfile(p) and hashlib.sha256(open(p, "rb").read()).hexdigest() == digest
        check(ok, f"protected file modified or missing: {rel}")
    for root, _, files in os.walk(PROJECT):
        for name in files:
            if name in ("Makefile", "GNUmakefile", "makefile") or name.endswith(".mk"):
                text = open(os.path.join(root, name), errors="replace").read()
                check(".NOTPARALLEL" not in text and "MAKEFLAGS" not in text,
                      f"{name}: parallelism must not be disabled or overridden")


def test_clean_parallel_builds():
    for i in range(3):
        d = fresh_copy(slow_generator=True)
        r = make(d)
        if not check(r.returncode == 0, f"clean -j16 build #{i} failed: {r.stderr[-600:]}"):
            return
        check_binaries(d, f"clean build #{i}")
        check_noop(d, f"after clean build #{i}")
    d = fresh_copy()
    r = make(d, jobs=1)
    check(r.returncode == 0, "serial clean build failed")
    check_binaries(d, "serial build")


def test_incremental():
    d = fresh_copy()
    if not check(make(d).returncode == 0, "incremental: initial build failed"):
        return
    check_noop(d, "initial")
    for src, n in EXPECTED_RECOMPILES.items():
        before = snapshot(d)
        touch(os.path.join(d, src))
        r = make(d)
        check(r.returncode == 0, f"rebuild after touching {src} failed")
        after = snapshot(d)
        objs = changed(before, after, ".o")
        check(len(objs) == n, f"touching {src} recompiled {len(objs)} objects, expected {n}: {objs}")
        bins = [b for b in ("bin/logstat", "bin/logstat-debug") if b in changed(before, after)]
        check(len(bins) == 2, f"touching {src} did not relink both programs")
        check_binaries(d, f"after touching {src}")
        check_noop(d, f"after touching {src}")

    before = snapshot(d)
    with open(os.path.join(d, "VERSION"), "w") as f:
        f.write("2.0.0\n")
    check(make(d).returncode == 0, "rebuild after VERSION change failed")
    objs = changed(before, snapshot(d), ".o")
    check(len(objs) == 2, f"VERSION change recompiled {len(objs)} objects, expected 2: {objs}")
    check_binaries(d, "after VERSION change", version="2.0.0")
    check_noop(d, "after VERSION change")

    # Change the struct layout: any stale object would read fields at old offsets.
    p = os.path.join(d, "include", "record.h")
    text = open(p).read()
    old = "    int level;\n    int line_no;\n    char msg[MSG_MAX];\n"
    new = "    char msg[MSG_MAX];\n    long pad;\n    int line_no;\n    int level;\n"
    check(old in text, "record.h layout block not found")
    time.sleep(0.05)
    open(p, "w").write(text.replace(old, new))
    check(make(d).returncode == 0, "rebuild after struct layout change failed")
    check_binaries(d, "after struct layout change", version="2.0.0")


def main():
    os.makedirs(os.path.dirname(REWARD), exist_ok=True)
    try:
        test_static()
        test_clean_parallel_builds()
        test_incremental()
    except Exception as e:  # any crash or timeout is a fail
        failures.append(f"verifier error: {e!r}")
        print("FAIL:", e)
    ok = not failures
    print("PASS" if ok else f"{len(failures)} check(s) failed")
    open(REWARD, "w").write("1" if ok else "0")


if __name__ == "__main__":
    main()
