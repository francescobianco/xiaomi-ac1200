#!/bin/sh
# Elimina solo i file temporanei introdotti dai nostri script.
umask 077
report=/tmp/xiaomi-lab-cleanup.txt
{
echo '=== identity ==='
id
echo '=== cleanup ==='
rm -f /tmp/xiaomi-lab-inventory.txt /tmp/xiaomi-lab-tools.txt /tmp/xiaomi-lab-backup-report.txt /tmp/xiaomi-lab-nand.bin
rm -f /tmp/speedtest_urls.xml
echo 'Temporary laboratory data removed; stock fallback speed-test list may be used.'
echo 'No SSH installation, password-root change, NVRAM write or firmware flash requested.'
} > "$report" 2>&1
curl --noproxy '*' -f -s --connect-timeout 3 --max-time 12 --data-binary @"$report" http://192.168.31.222:18080/inventory >/dev/null
rm -f "$report" /tmp/script.sh
