# Passaggio di consegne — Xiaomi R3

**Aggiornato: 10 novembre 2026, 19:40 — prima build locale RIUSCITA (Linux 6.18.60). Leggere questo file prima di operare.**

## Obiettivo e autorizzazioni

Francesco vuole Linux moderno sul suo Xiaomi R3 e poi VPN/WireGuard, con sorgenti e aggiornamenti mantenibili. Ha autorizzato configurazione e accesso software **senza seriale per adesso**, inventario, backup e prosecuzione dell'analisi/build. Prima di un flash preparare immagine, hash, layout e recupero concreti e concordarne l'esecuzione: non è stata ancora proposta un'immagine da installare.

Non installare firmware alla cieca, non sostituire bootloader e non cambiare flag NVRAM per tentativi. Non chiedere nuovamente se possiamo lavorare senza seriale: è già stato deciso. Non è stata ancora dimostrata una recovery senza seriale.

## Stato del router

- R3 confermato da API, firmware cinese **2.26.39**, kernel stock 2.6.36, 128 MB RAM, NAND 128 MiB; etichetta fisica non ancora verificata.
- Configurazione iniziale completata. Wi-Fi `Xiaomi-R3-Lab`; password Wi-Fi e amministrazione distinte, casuali, in **`private/credentials.json`** (0600, directory 0700, esclusa da Git). NON stampare credenziali/token nei log.
- PC: Internet su `eno1`, 192.168.144.10/24, gateway 192.168.144.1. Dongle `wlxe0b2f1c5819b`: 192.168.31.222/24, profilo `xiaomi-lab`, senza default route o DNS; router 192.168.31.1. Verificare indirizzi prima di riusare i callback.
- **Esecuzione root ottenuta via API stock c_upload/netspeed**, callback uid=0 e inventario verificati. SSH/Telnet NON installati; porte 22/23/122 rifiutano connessione. Nessuna modifica esplicita a password root, bootloader o NVRAM nella procedura di accesso.
- `scripts/probe_access.py --script SCRIPT` esegue uno script revisionato come root e raccoglie `/inventory` HTTP in `private/initial-inventory.txt`. Questo file viene sovrascritto: preservare i rapporti importanti con altro nome.
- L'upload restituisce **code 1629**, ma l'esecuzione funziona comunque; successo provato dal callback, non dal codice upload. Serve XML multilinea e script in background; la causa precisa rispetto al primo tentativo non è stata isolata.
- Gli script recenti rimuovono i file temporanei del laboratorio dopo il trasferimento; il server HTTP sul PC si chiude al termine del comando.

## Backup: cosa esiste davvero

- `backups/2026-11-10/full-ecc.bin`: **134217728 byte**, NAND logica completa con ECC; hash in `full-ecc.sha256`.
- 32 file `ecc-00.bin` ... `ecc-31.bin`, 4 MiB ciascuno. MD5 calcolati sul router e verificati sul PC, SHA-256 locali in manifest e SHA256SUMS.
- `verify-00.bin`: seconda lettura primi 4 MiB; Bootloader, Config, Bdata e Factory identici byte per byte.
- **RAW/OOB FALLITO** sul primo blocco con errore I/O mtd_read. Non esiste una copia raw valida. `verify_backups.py` esce 1 per questo limite e conferma separatamente `logical_ecc_backup_verified=true`.
- Overlay acquisito online, non snapshot atomico. Ripristino NON provato. Seconda copia su supporto indipendente ancora da creare (non basta lo stesso SSD).
- Dump e credenziali sono esclusi da Git. Non pubblicarli. I rapporti pubblici depurati sono in `docs/evidence/`.

## Scoperta importante: esiste una base moderna

La prima ricognizione web era incompleta. **Il clone Git attuale X-Wrt contiene R3 e driver NAND per kernel 6.18.60.** Non occorre partire dal solo OpenWrt 21.02.

- Sorgenti: `work/x-wrt`, repository `https://github.com/x-wrt/x-wrt.git`.
- Commit fissato: **`61de4809b444b7a3d3c0a9cc27c1e0d6702572e4`**.
- Target `ramips/mt7620`, profilo `xiaomi_miwifi-r3`, CPU mipsel_24kc.
- Seed: `configs/r3-lab.seed`; configurazione espansa reale: `configs/r3-lab.expanded.config`.
- Lock con hash: `configs/sources.lock.json`; archivi scaricati: `configs/downloads.sha256`.
- Nessun feed installato per la build minima; warning su dipendenze opzionali non selezionate. Download completato (~493 MiB, 91 archivi inventariati).
- Output atteso: `work/x-wrt/bin/targets/ramips/mt7620/`.

## Build: storico dell'errore util-linux (RISOLTO, vedi docs/BUILD.md)

Comando avviato: `bash scripts/build_lab.sh -j8 > work/build.log 2>&1`.

**Storico:** la prima build era terminata con exit code 2. Nessuna build completa lasciata attiva; la precedente sessione `61781` è conclusa. Il problema osservato è `ERROR: tools/util-linux failed to build`. Non è stata prodotta un'immagine pronta da installare.

Diagnosi concreta già effettuata con:

```bash
work/x-wrt/staging_dir/host/bin/ninja -C work/x-wrt/build_dir/host/util-linux-2.42.2/openwrt-build -j1
```

Errore in `lib/colors.c`: **`cur_term` undeclared**, dichiarazioni mancanti setupterm/tigetnum/del_curterm. La riga di compilazione usa percorsi ncurses di **Homebrew** (`/home/linuxbrew/.linuxbrew/opt/ncurses/...`) e non include il nostro sysroot.

Sul PC manca libncurses-dev. Sudo richiede password; nessun pacchetto è stato installato nel sistema. Pacchetto Ubuntu ufficiale già scaricato ed estratto:

- `work/host-packages/libncurses-dev_6.4+20240113-1ubuntu2.2_amd64.deb`
- `work/host-sysroot/usr/include`, `work/host-sysroot/usr/lib/x86_64-linux-gnu`

Il wrapper inizialmente esportava HOST_EXTRA_CFLAGS/HOST_EXTRA_LDFLAGS nell'ambiente, ma **rules.mk li riassegna da CONFIG_HOST_EXTRA_* alle righe 344/347**: gli export non bastano! Correggere passando queste variabili come argomenti make (override command line), e controllare i percorsi ncurses di pkg-config/Meson. Non inquinare il cross compiler MIPS con CPATH globale.

Log Meson:
`work/x-wrt/build_dir/host/util-linux-2.42.2/openwrt-build/meson-logs/meson-log.txt`.
Configurazione host generata:
`work/x-wrt/build_dir/host/util-linux-2.42.2/openwrt-native.txt`.

### Prossimi passi della build

- [x] Wrapper aggiornato: Homebrew rimosso dal PATH (Meson trovava `ncursesw6-config` di Linuxbrew) e HOST_EXTRA_CFLAGS/LDFLAGS passati come override make.
- [x] Prima make completa conclusa: exit code 2, errore host util-linux. Nessuna make completa ancora attiva.
- [x] `tools/util-linux/clean` + `compile -j1 V=s` riusciti (log `work/util-linux-fix.log`): Meson trova curses 6.4 del sysroot Ubuntu, `HAVE_NCURSES_H`/`HAVE_TERM_H` attivi, nessun percorso linuxbrew.
- [x] Build ripresa (`work/build-resume.log`): **exit=0** alle 19:29, nessun altro errore dopo il fix di util-linux.
- [x] Build portata a termine; l'unico fix necessario è quello riproducibile nel wrapper.
- [x] Immagini verificate (dettagli in RECAP.md): sha256sums OK; kernel1 di 2,62 MiB con CRC OK; initramfs di 6,06 MiB (solo avvio da RAM); 107 pacchetti, senza LuCI né WireGuard. Nessun flash.
- [x] TODO, BUILD.md, REGISTRO.md e README aggiornati con l'esito effettivo; checksum e manifest in `configs/`.

### Prossimi passi (da concordare con Francesco)

- [ ] Decidere le aggiunte all'immagine: WireGuard (`wireguard-tools`, `kmod-wireguard`), chiave SSH autorizzata, password root, eventuale LuCI. Valutare Image Builder/ccache e `-j12`.
- [ ] Piano di installazione e recupero: quale immagine e quale layout (UBI standard o variante slot1), fallback dello stock, copia indipendente del backup.

## Recupero e avvio: risultati e limiti

- Bootloader: stringa U-Boot 1.1.3 (12 aprile 2016). Contiene menu TFTP; non è dimostrato come selezionarlo senza console.
- Entrambi i kernel stock hanno uImage header e payload con CRC validi; script offline `scripts/analyze_backup.py`.
- Parametri letti (NON modificati): flag_boot_rootfs=0, flag_last_success=0, flag_boot_success=1, flag_try_sys1_failed=0, flag_try_sys2_failed=0, boot_wait=off, uart_en=0, bootdelay=5, bootcmd=tftp.
- **Kexec stock non implementato**: sys_kexec_load è alias di sys_ni_syscall. Non promettere un boot initramfs via kexec.
- Device Tree standard X-Wrt: kernel_stock a 0x200000 (4 MiB), kernel a 0x600000 (4 MiB), UBI a **0xa00000, 118 MiB**. UBI unifica rootfs0/rootfs1/overlay: preservare solo kernel0 NON preserva lo stock avviabile.
- Possibile variante da studiare, NON implementata: kernel nuovo nello slot1 e UBI confinata a rootfs1, preservando kernel0/rootfs0/overlay. Richiede verificare bootloader/flag e upgrade; non assumerne il fallback.
- Il driver X-Wrt corrente non registra _read_oob/_write_oob. Indizio di limiti OOB; non prova la causa esatta dell'errore sul driver stock.

## File da leggere e strumenti

- `docs/BUILD.md`, `docs/RECUPERO.md`: base candidata e analisi layout.
- `docs/ACCESSO.md`, `docs/REGISTRO.md`: cronologia e procedura root.
- `scripts/README.md`: strumenti di configurazione e acquisizione.
- `private/recovery-readonly.txt`, `private/hardware-inventory.txt`, `private/backup-tools.txt`, `private/backup-report.txt`: rapporti tecnici integrali riservati.
- Riferimenti clonati: `work/r3-historical` (Baumgartl, kernel 4.14), `work/r3-build-reference` (BioXeon, ricette storiche). Non eseguire automaticamente i loro workflow.
- `.idea/` era preesistente: non modificarla; esclusa dal commit tramite .gitignore.
- Remoto: `https://github.com/francescobianco/xiaomi-ac1200`, branch `main`. Francesco ha richiesto commit e push di documenti/script/configurazioni; credenziali e dump devono rimanere locali. Per il commit corrente consultare `git log -1` e verificare il push con il tracking remoto.

**Regola di continuità:** aggiornare questa sezione e i checkbox dopo ogni esito significativo. Non scrivere “compilato” finché make non termina con successo e gli artefatti non sono controllati.


## Sequenza di ripresa consigliata

1. Leggere `work/build.log`, il wrapper e le righe HOST_EXTRA_* in `work/x-wrt/rules.mk`. Non riclonare o ricompilare da zero: cache e strumenti già costruiti sono riutilizzabili.
2. Correggere il wrapper affinché make riceva i flag host come variabili da riga di comando. Poi riconfigurare il solo util-linux: il vecchio file Meson ha memorizzato i percorsi errati. `tools/util-linux/clean` è un target di pulizia locale, non riguarda il router.
3. Compilare quel target con `-j1 V=s`, salvando il log in `work/util-linux-fix.log`. Controllare che gli include term.h/curses.h e il link provengano dal sysroot Ubuntu locale, senza assumere che gli export precedenti abbiano effetto.
4. Riprendere la build completa; correggere gli ulteriori errori eventualmente emersi e aggiornare questo file. Solo dopo il successo passare al controllo delle immagini e al piano di installazione.

Esempio di override make da valutare (NON ancora eseguito, non costituisce un fix verificato):

```bash
project_root="$PWD"
bash scripts/build_lab.sh tools/util-linux/clean
bash scripts/build_lab.sh tools/util-linux/compile -j1 V=s \
  HOST_EXTRA_CFLAGS="-I$project_root/work/host-sysroot/usr/include" \
  HOST_EXTRA_LDFLAGS="-L$project_root/work/host-sysroot/usr/lib/x86_64-linux-gnu" \
  > work/util-linux-fix.log 2>&1
```

Il wrapper va aggiornato per rendere persistente il fix anche nella build completa; una singola invocazione riuscita non basta a rendere la procedura riproducibile.

## Verifiche già eseguite

- [x] Configurazione stock e login con nuova password verificati.
- [x] Esecuzione root e inventario ricevuti.
- [x] Backup ECC completo e seconda lettura delle aree critiche verificati.
- [x] Hash combinato e CRC dei due kernel stock validi.
- [x] Checkout X-Wrt fissato e presenza di profilo/driver R3 verificata.
- [x] Prerequisiti host e generazione defconfig riusciti.
- [x] Download completato; configurazione attuale uguale all'hash del lock.
- [x] Controlli sintattici Python/shell e `git diff --check` superati prima del commit.
- [x] Build completa riuscita (10/11/2026 19:29, Linux 6.18.60, r0-61de480).
- [ ] Artefatti controllati e configurazione di accesso sicura predisposta per l'immagine.
- [ ] Recovery concreta definita e copia indipendente del backup disponibile.
- [ ] Primo avvio del sistema nuovo.
- [ ] Ethernet/Wi-Fi/USB e persistenza verificati.
- [ ] WireGuard configurato e prestazioni misurate.
- [ ] Aggiornamento tra due build e recupero da configurazione errata provati.
