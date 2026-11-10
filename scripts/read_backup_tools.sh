#!/bin/sh
# Sola lettura; output temporaneo e trasferimento al PC del laboratorio.
umask 077
{
echo '=== nanddump ==='
nanddump --help 2>&1
echo '=== flash sysfs ==='
for d in /sys/class/mtd/mtd[0-9]*; do
    echo "$d"
    for f in name size erasesize writesize oobsize ecc_strength ecc_step_size bad_blocks bbt_blocks corrected_bits ecc_failures; do
        if [ -r "$d/$f" ]; then echo "$f=$(cat "$d/$f")"; fi
    done
done
echo '=== partition offsets ==='
dmesg | grep -A 15 'Creating 13 MTD'
echo '=== transfer tools ==='
command -v sha256sum
command -v md5sum
curl --version
echo '=== mounts ==='
mount
} > /tmp/xiaomi-lab-tools.txt 2>&1
curl --noproxy '*' -s --connect-timeout 3 --max-time 12 --data-binary @/tmp/xiaomi-lab-tools.txt http://192.168.31.222:18080/inventory >/dev/null
