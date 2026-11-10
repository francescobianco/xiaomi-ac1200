#!/bin/bash
# Diagnosi in sola lettura di X-Wrt dal lato LAN (192.168.15.1), via SSH con chiave.
# Rapporto in private/xwrt-diag-<data>.txt. Non modifica la configurazione.
set -euo pipefail
project_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
host=${1:-192.168.15.1}
out="$project_root/private/xwrt-diag-$(date +%Y%m%d-%H%M).txt"
umask 077
ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new root@"$host" '
echo "=== release ==="; cat /etc/openwrt_release; uname -a; uptime
echo "=== mtd / ubi ==="; cat /proc/mtd; ubinfo -a 2>&1 | head -40; df -h
echo "=== fw_printenv flags ==="; fw_printenv 2>&1 | grep -E "^(flag_|boot_wait|uart_en|bootdelay)"
echo "=== board.d ==="; ls -l /etc/board.d/
echo "=== board.json wlan ==="; jsonfilter -i /etc/board.json -e "@.wlan" 2>&1
echo "=== wireless (chiavi oscurate) ==="; uci show wireless 2>&1 | sed -E "s/(\.key=).*/\1<oscurata>/"
echo "=== wifi status ==="; wifi status 2>&1 | head -80
echo "=== iw ==="; iw dev 2>&1; iw phy 2>&1 | grep -E "Wiphy|Band|MHz \[" | head -30
echo "=== dmesg radio ==="; dmesg | grep -i -E "rt2800|mt76|wmac|phy[0-9]|ieee80211|firmware|eeprom" | head -60
echo "=== logread wifi/hostapd ==="; logread 2>/dev/null | grep -i -E "hostapd|wpa|wifi|netifd|mac80211|board" | tail -80
echo "=== uci-defaults residui ==="; ls -l /etc/uci-defaults/ 2>&1
echo "=== dropbear ==="; uci show dropbear
echo "=== rete ==="; ip -br addr; ip route
' > "$out" 2>&1
echo "Rapporto: $out"
