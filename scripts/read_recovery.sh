#!/bin/sh
# Sola lettura di parametri selezionati: non modifica l'ambiente di avvio.
umask 077
report=/tmp/xiaomi-lab-recovery.txt
{
echo '=== boot flags (read only) ==='
for name in flag_boot_rootfs flag_last_success flag_boot_success flag_try_sys1_failed flag_try_sys2_failed boot_wait uart_en bootdelay bootcmd; do
    printf '%s=' "$name"
    nvram get "$name"
done
echo '=== kexec config ==='
if [ -r /proc/config.gz ]; then zcat /proc/config.gz | grep -E 'CONFIG_(KEXEC|RELOCATABLE)'; else echo 'kernel config unavailable'; fi
echo '=== kexec symbols ==='
grep -E ' (sys_kexec_load|kernel_kexec|machine_kexec)$' /proc/kallsyms | sed 's/^[^ ]* /ADDRESS /'
awk '$3 == "sys_kexec_load" { k=$1 } $3 == "sys_ni_syscall" { n=$1 } END { if (k != "" && n != "") print "kexec_load_aliases_ni_syscall=" (k == n ? "yes" : "no"); else print "kexec_alias_check=unavailable" }' /proc/kallsyms
echo '=== recovery tools ==='
for path in /sbin/kexec /usr/sbin/kexec /sbin/sysupgrade /lib/upgrade /usr/lib/lua/luci/controller/api/misystem.lua; do
    ls -ld "$path" 2>&1
done
} > "$report" 2>&1
curl --noproxy '*' -f -s --connect-timeout 3 --max-time 12 --data-binary @"$report" http://192.168.31.222:18080/inventory >/dev/null
rm -f "$report" /tmp/script.sh /tmp/speedtest_urls.xml
