#!/bin/sh
# Usage: genversion.sh VERSION_FILE  -- writes a C header to stdout.
v=$(cat "$1")
printf '#ifndef VERSION_H\n#define VERSION_H\n#define LOGSTAT_VERSION "%s"\n#endif\n' "$v"
