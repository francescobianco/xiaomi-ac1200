#!/bin/sh
# Verifiche in SOLA LETTURA per il piano di installazione (fase A3).
# Nessun nvram set/commit, nessuna scrittura mtd, nessun riavvio.
umask 077
report=/tmp/xiaomi-lab-install-checks.txt
{
echo '=== system ==='
uname -a
cat /proc/cmdline
echo '=== boot flags ==='
for name in flag_boot_rootfs flag_last_success flag_boot_success flag_try_sys1_failed flag_try_sys2_failed flag_ota_reboot flag_boot_type boot_wait uart_en bootdelay; do
    printf '%s=' "$name"; nvram get "$name"
done
echo '=== files referencing boot flags ==='
files=$(grep -rl -E 'flag_last_success|flag_boot_rootfs|flag_try_sys' /sbin /bin /usr/sbin /usr/bin /lib /etc /usr/lib/lua 2>/dev/null)
echo "$files"
for f in $files; do
    case "$f" in *.so*|*.ko) continue ;; esac
    echo "--- $f"
    grep -n -E 'flag_last_success|flag_boot_rootfs|flag_try_sys|flag_boot_success|flag_ota_reboot|mtd write|kernel0|kernel1|rootfs0|rootfs1' "$f" 2>/dev/null | head -60
done
echo '=== flash/upgrade scripts (full, size-limited) ==='
for f in /usr/sbin/flash.sh /lib/upgrade/libupgrade.sh /lib/upgrade/common.sh; do
    [ -f "$f" ] || continue
    echo "--- $f ($(wc -c < "$f") bytes)"
    head -c 24000 "$f"
done
echo '=== reset button ==='
gpiobtn=$(cat /proc/xiaoqiang/reset 2>&1)
echo "reset_gpio=$gpiobtn"
gpio "$gpiobtn" 2>&1
echo "model=$(cat /proc/xiaoqiang/model 2>&1) ft_mode=$(cat /proc/xiaoqiang/ft_mode 2>&1)"
echo '=== mtd ==='
cat /proc/mtd
for n in 8 9 10 11 12; do
    for a in ecc_failures corrected_bits bad_blocks bbt_blocks; do
        [ -r /sys/class/mtd/mtd$n/$a ] && echo "mtd$n $a=$(cat /sys/class/mtd/mtd$n/$a)"
    done
done
echo '=== kernel log: bad blocks / ubi / nand ==='
dmesg | grep -i -E 'bad (erase)?block|bad peb|ecc|ubi[0-9]?:.*(bad|error|attached)|nand' | head -60
echo '=== tools ==='
for t in mtd nanddump nandwrite flash_erase ubiformat md5sum sha256sum sha1sum curl wget; do
    printf '%s: ' "$t"; which "$t" 2>/dev/null || echo missing
done
mtd 2>&1 | head -30
echo '=== free space /tmp ==='
df -k /tmp
free
} > "$report" 2>&1
curl --noproxy '*' -f -s --connect-timeout 3 --max-time 20 --data-binary @"$report" http://192.168.31.222:18080/inventory >/dev/null
rm -f "$report" /tmp/script.sh /tmp/speedtest_urls.xml
