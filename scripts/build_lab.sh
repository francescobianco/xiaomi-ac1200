#!/bin/bash
# Build locale; non comunica con il router e non installa immagini.
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
host_root="$project_root/work/host-sysroot/usr"
host_inc="$host_root/include"
host_lib="$host_root/lib/x86_64-linux-gnu"

# Homebrew nel PATH contamina gli strumenti host: Meson trovava
# ncursesw6-config di Linuxbrew e mescolava header/librerie estranei.
clean_path=$(printf '%s' "$PATH" | tr ':' '\n' | grep -v -e linuxbrew -e '^$' | paste -sd: -)
export PATH="$clean_path"
unset HOMEBREW_PREFIX HOMEBREW_CELLAR HOMEBREW_REPOSITORY INFOPATH \
      PKG_CONFIG_PATH PKG_CONFIG_LIBDIR CPATH C_INCLUDE_PATH LIBRARY_PATH

# rules.mk riassegna HOST_EXTRA_* da CONFIG_HOST_EXTRA_*: un export non basta,
# servono override da riga di comando di make (valgono solo per gli strumenti
# host, non per il cross compiler MIPS).
host_overrides=(
    "HOST_EXTRA_CFLAGS=-I$host_inc"
    "HOST_EXTRA_LDFLAGS=-L$host_lib -Wl,-rpath-link,$host_lib"
)

sync_files() {
    # Overlay dell'immagine: configs/files (versionato) + chiave SSH pubblica
    # da private/ (fuori da Git). Ricreato a ogni build per restare riproducibile.
    local keys="$project_root/private/router_authorized_keys"
    local dest="$project_root/work/x-wrt/files"
    if [[ ! -s "$keys" ]]; then
        echo "ERRORE: manca $keys (chiave pubblica SSH per il router)." >&2
        echo "Senza chiave l'immagine non avrebbe alcun accesso SSH (password disattivate)." >&2
        exit 1
    fi
    rm -rf -- "$dest"
    cp -a -- "$project_root/configs/files" "$dest"
    install -d -m 700 "$dest/etc/dropbear"
    install -m 600 "$keys" "$dest/etc/dropbear/authorized_keys"
}

case "${1:-}" in
    prereq|defconfig|oldconfig|menuconfig)
        # Il controllo dei prerequisiti usa gcc senza HOST_EXTRA_*.
        export CPATH="$host_inc"
        export LIBRARY_PATH="$host_lib"
        host_overrides=()
        ;;
    *clean|download|*/download|tools/*|toolchain/*) ;;
    *) sync_files ;;
esac
cd "$project_root/work/x-wrt"
exec make "$@" "${host_overrides[@]}"
