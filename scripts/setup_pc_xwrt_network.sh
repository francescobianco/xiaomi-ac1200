#!/bin/bash
# Crea sul PC il profilo NetworkManager "xwrt-lab" per raggiungere X-Wrt
# (192.168.15.1) tramite il dongle Wi-Fi. Non tocca eno1 né il profilo
# xiaomi-lab, non aggiunge route predefinite né DNS. Va eseguito con sudo
# (da SSH polkit nega la modifica). Idempotente: se il profilo esiste esce.
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
conf="$project_root/private/router_wifi.conf"
ifname=wlxe0b2f1c5819b

if nmcli -t -f NAME con show | grep -qx xwrt-lab; then
    echo "Profilo xwrt-lab già presente: nessuna modifica."
    exit 0
fi
ssid=$(sed -n 's/^WIFI_SSID=//p' "$conf")
key=$(sed -n 's/^WIFI_KEY=//p' "$conf")
[[ -n "$ssid" && -n "$key" ]] || { echo "SSID o password mancanti in $conf" >&2; exit 1; }

nmcli con add type wifi con-name xwrt-lab ifname "$ifname" ssid "$ssid" \
    wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$key" \
    ipv4.method manual ipv4.addresses 192.168.15.10/24 \
    ipv4.never-default yes ipv4.ignore-auto-dns yes \
    ipv6.method disabled \
    connection.autoconnect yes connection.autoconnect-priority 10 >/dev/null
echo "Creato xwrt-lab: $ifname 192.168.15.10/24, senza gateway né DNS, autoconnessione attiva."
