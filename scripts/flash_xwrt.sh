#!/bin/sh
# FASE B — installazione X-Wrt sullo stock R3 (docs/INSTALLAZIONE.md).
# Scrive kernel1 e rootfs0, imposta flag_last_success=1, boot_wait=on, uart_en=1.
# Non tocca Bootloader, Config (oltre ai 3 flag), Factory, kernel0.
PC=http://192.168.31.222:18081
K_MD5=40b6070da3ac5f70f3923ed9a9dd4a9b
K_SIZE=2745655
R_MD5=8ba5be646d74bb5023c53b3985453841
R_SIZE=4980736
W=/tmp/xwrt
RAM=/tmp/xwrt-ram
LOG=$W/log.txt

mkdir -p $W && cd $W || exit 1
: > $LOG
log() { echo "$(date +%T) $*" >> $LOG; }
report() { curl --noproxy '*' -s --connect-timeout 3 --max-time 10 --data-binary @$LOG "$PC/report/$1" >/dev/null 2>&1; }
abort() { log "ABORT: $*"; report abort; exit 1; }

log "inizio; flag: last_success=$(nvram get flag_last_success) boot_rootfs=$(nvram get flag_boot_rootfs)"

# 1. download e verifica
for f in kernel1.bin rootfs0.bin; do
    curl --noproxy '*' -s -f --max-time 120 -o $f "$PC/$f" || abort "download $f fallito"
done
km=$(md5sum kernel1.bin | cut -d' ' -f1); rm_=$(md5sum rootfs0.bin | cut -d' ' -f1)
ks=$(wc -c < kernel1.bin); rs=$(wc -c < rootfs0.bin)
log "kernel1 md5=$km size=$ks ; rootfs0 md5=$rm_ size=$rs"
[ "$km" = "$K_MD5" ] && [ "$ks" = "$K_SIZE" ] || abort "kernel1 non corrisponde"
[ "$rm_" = "$R_MD5" ] && [ "$rs" = "$R_SIZE" ] || abort "rootfs0 non corrisponde"
grep -q '"kernel1"' /proc/mtd && grep -q '"rootfs0"' /proc/mtd || abort "partizioni non trovate"

# 2. ambiente in RAM per la scrittura di rootfs0 (prima di qualsiasi scrittura)
. /lib/upgrade/common.sh
RAM_ROOT=$RAM
rm -rf $RAM; mkdir -p $RAM/dev $RAM/proc $RAM/tmp $RAM/lib
install_bin /bin/busybox /bin/sh /bin/ash /bin/sync /bin/cat /bin/echo /bin/date /bin/grep /bin/sleep /usr/bin/md5sum /sbin/reboot
install_bin /sbin/mtd
install_bin /usr/bin/curl
for l in /lib/ld-uClibc.so.0 /lib/libc.so.0 /lib/libgcc_s.so.1; do [ -e $l ] && cp -L $l $RAM$l; done
cp rootfs0.bin $RAM/rootfs0.bin
mount -o bind /dev $RAM/dev || abort "bind /dev fallito"
mount -t proc proc $RAM/proc || abort "mount proc fallito"
chroot $RAM /bin/busybox true || abort "chroot busybox non funziona"
chroot $RAM /sbin/mtd 2>&1 | grep -q 'Usage' || abort "chroot mtd non funziona"
chroot $RAM /bin/grep -q x /proc/mtd 2>/dev/null; [ $? -le 1 ] || abort "chroot grep non funziona"
chroot $RAM /usr/bin/curl --version >/dev/null 2>&1 && log "curl in RAM ok" || log "curl in RAM non disponibile (niente rapporto finale)"
log "ambiente RAM pronto ($(du -s $RAM | cut -f1) KiB)"
report pre

# 3. kernel1 (rootfs0 ancora intatto: in caso di errore lo stock resta avviabile)
mtd write kernel1.bin kernel1 >> $LOG 2>&1 || abort "mtd write kernel1 fallito"
mtd verify kernel1.bin kernel1 > $W/vk.txt 2>&1; cat $W/vk.txt >> $LOG
grep -q '^Success' $W/vk.txt || abort "verify kernel1 fallito (mtd non stampa Success)"
log "kernel1 scritto e verificato"

# 4. flag
nvram set flag_last_success=1
nvram set boot_wait=on
nvram set uart_en=1
nvram commit
log "flag: last_success=$(nvram get flag_last_success) boot_wait=$(nvram get boot_wait) uart_en=$(nvram get uart_en)"
report kernel

# 5. rootfs0 dall'ambiente in RAM, poi riavvio
cp $LOG $RAM/log.txt
chroot $RAM /bin/busybox sh -c '
L=/log.txt
/sbin/mtd write /rootfs0.bin rootfs0 >> $L 2>&1 && echo "rootfs0 scritto" >> $L || echo "ERRORE write rootfs0" >> $L
/sbin/mtd verify /rootfs0.bin rootfs0 > /vr.txt 2>&1; cat /vr.txt >> $L; grep -q "^Success" /vr.txt && echo "rootfs0 verificato" >> $L || echo "ERRORE verify rootfs0" >> $L
echo "riavvio" >> $L
/usr/bin/curl --noproxy "*" -s --connect-timeout 3 --max-time 10 --data-binary @$L http://192.168.31.222:18081/report/final >/dev/null 2>&1
/bin/busybox sync
/bin/busybox sleep 2
/bin/busybox reboot -f
'
