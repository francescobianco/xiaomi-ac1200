#!/bin/sh
# Lettura NAND in blocchi da 4 MiB: mai un dump completo nella RAM del router.
umask 077
report=/tmp/xiaomi-lab-backup-report.txt
chunk=/tmp/xiaomi-lab-nand.bin
base=http://192.168.31.222:18080
exec > "$report" 2>&1
echo '=== geometry ==='
for f in size writesize oobsize erasesize; do echo "$f=$(cat /sys/class/mtd/mtd0/$f)"; done
echo '=== acquisition ==='
run_backup() {
    kind=$1
    number=0
    offset=0
    while [ "$number" -lt 32 ]; do
        name=$(printf '%s-%02d.bin' "$kind" "$number")
        echo "BEGIN $name offset=$offset length=4194304"
        if [ "$kind" = ecc ]; then
            nanddump --bb=padbad --omitoob --startaddress="$offset" --length=4194304 --file="$chunk" /dev/mtd0 || return 1
        else
            nanddump --bb=dumpbad --noecc --oob --startaddress="$offset" --length=4194304 --file="$chunk" /dev/mtd0 || return 1
        fi
        wc -c "$chunk"
        md5sum "$chunk"
        curl --noproxy '*' -f -s --connect-timeout 3 --max-time 60 --data-binary @"$chunk" "$base/backup/$name" || return 1
        echo "SENT $name"
        rm -f "$chunk"
        number=$((number + 1))
        offset=$((offset + 4194304))
    done
}
run_backup ecc
ecc_status=$?
echo "ECC_STATUS=$ecc_status"
if [ "$ecc_status" -eq 0 ]; then
    run_backup raw
    raw_status=$?
    echo "RAW_STATUS=$raw_status"
    # Seconda lettura dei primi 4 MiB per confrontare bootloader e Factory.
    nanddump --bb=padbad --omitoob --startaddress=0 --length=4194304 --file="$chunk" /dev/mtd0
    echo "VERIFY_DUMP_STATUS=$?"
    md5sum "$chunk"
    curl --noproxy '*' -f -s --connect-timeout 3 --max-time 60 --data-binary @"$chunk" "$base/backup/verify-00.bin"
    echo "VERIFY_UPLOAD_STATUS=$?"
fi
rm -f "$chunk"
echo '=== kernel after acquisition ==='
dmesg | tail -40
echo '=== complete ==='
curl --noproxy '*' -f -s --connect-timeout 3 --max-time 15 --data-binary @"$report" "$base/inventory" >/dev/null
