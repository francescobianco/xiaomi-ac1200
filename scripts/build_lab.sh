#!/bin/bash
# Build locale; non comunica con il router e non installa immagini.
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
host_root="$project_root/work/host-sysroot/usr"
export HOST_EXTRA_CFLAGS="-I$host_root/include ${HOST_EXTRA_CFLAGS:-}"
export HOST_EXTRA_LDFLAGS="-L$host_root/lib/x86_64-linux-gnu ${HOST_EXTRA_LDFLAGS:-}"
# Il controllo iniziale usa gcc senza HOST_EXTRA_*; non propagare questi
# percorsi tramite CPATH ai compilatori MIPS durante la build del firmware.
case "${1:-}" in
    prereq|defconfig|oldconfig|menuconfig)
        export CPATH="$host_root/include${CPATH:+:$CPATH}"
        export LIBRARY_PATH="$host_root/lib/x86_64-linux-gnu${LIBRARY_PATH:+:$LIBRARY_PATH}"
        ;;
esac
cd "$project_root/work/x-wrt"
exec make "$@"
