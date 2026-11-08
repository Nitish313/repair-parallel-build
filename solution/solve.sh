#!/bin/bash
set -euo pipefail
cd /app/project
# Replace the recursive build with one correct top-level Makefile.
cp /solution/Makefile Makefile
rm -f lib/Makefile
make clean
make -j"$(nproc)"
./bin/logstat < sample.log
