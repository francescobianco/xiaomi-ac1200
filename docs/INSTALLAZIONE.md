# Piano di installazione e recupero — X-Wrt su Xiaomi R3

**Stato: PROPOSTA, non eseguita.** Redatta il 10 novembre 2026 sulla base del backup e dei sorgenti. Nessun comando di questo documento è stato eseguito sul router. La fase B richiede un via libera esplicito di Francesco.

## 1. Cosa abbiamo scoperto analizzando il backup

### Il bootloader non ha una recovery utilizzabile senza seriale

Le stringhe di U-Boot 1.1.3 (12/04/2016) mostrano solo il menu Ralink classico: comandi TFTP verso la RAM o la flash e una riga di comando. Il menu si apre con un tasto sulla console seriale (`boot_wait=off`, `uart_en=0`). Non ci sono riferimenti a USB, al tasto reset o a `miwifi.bin`. C'è invece la logica a due sistemi: `Booting System 1/2`, il controllo CRC di entrambi i kernel, `Boot failure detected on both systems` e i flag `flag_last_success`, `flag_boot_rootfs`, `flag_try_sys1_failed`, `flag_try_sys2_failed`.

### La recovery USB di Xiaomi sta nel kernel stock

Entrambi i kernel stock (kernel0 e kernel1, Linux 2.6.36) contengono un initramfs con `init` e `bin/usb_recovery.sh`. Il file `init`:

1. entra in **recovery** se, all'avvio, il **tasto reset è premuto** oppure se c'è una chiavetta USB con una sola partizione FAT ed etichetta OEM `miusbkit` (modalità automatica con `rom/ver_info.txt`);
2. entra in recovery anche quando `flag_try_sys1_failed=1` e `flag_try_sys2_failed=1`, cioè quando entrambi i sistemi risultano guasti; in quel caso attende la pressione del reset;
3. altrimenti monta `rootfs0` o `rootfs1` secondo `flag_boot_rootfs`. Se il mount fallisce, imposta `flag_try_sysN_failed=1` e riavvia.

In recovery, `usb_recovery.sh`:

- monta la chiavetta (`/dev/sda`) e prende i `*.bin`;
- li valida con `mkxqimage`, che controlla la **firma RSA di Xiaomi** (`/usr/share/xiaoqiang/public.pem`);
- scrive kernel0, kernel1, rootfs0, rootfs1, crash e, se presente nell'immagine, il bootloader; poi cancella overlay e azzera i flag di guasto.

**Conseguenza chiave:** la recovery dipende solo da un **kernel stock integro avviato dal bootloader**, non da rootfs0. Se preserviamo kernel0, la via di ritorno allo stock resta disponibile, a patto di avere un firmware R3 ufficiale firmato su chiavetta.

### I flag di avvio si possono modificare dal nuovo sistema

La partizione `Config` (0x40000) è un ambiente U-Boot standard: header CRC32 valido su 0x1000 byte, 45 variabili, compresi tutti i flag. Il pacchetto `uboot-envtools` incluso nell'immagine X-Wrt è configurato per l'R3 su `/dev/mtd1 0x0 0x1000 0x20000`. Da X-Wrt `fw_printenv` e `fw_setenv` possono quindi leggere e rimettere i flag per tornare al kernel stock.

## 2. Via proposta: layout standard X-Wrt con kernel0 stock preservato

È la via usata dalla comunità X-Wrt per l'R3 (vedi `work/r3-build-reference/README.md`): scrivere **kernel1** e **rootfs0**, lasciando intatti bootloader, Config, Factory e **kernel0**.

| Area | Offset | Prima | Dopo |
| --- | --- | --- | --- |
| Bootloader, Config, Bdata, Factory, crash | 0x0–0x200000 | stock | invariate (Config solo per 3 flag) |
| kernel0 | 0x200000 | kernel stock + recovery USB | **invariato** (`kernel_stock` per X-Wrt) |
| kernel1 | 0x600000 | kernel stock di riserva | **kernel X-Wrt 6.18.60** |
| rootfs0 + rootfs1 + overlay | 0xa00000–0x8000000 | UBI stock | **UBI X-Wrt da 118 MiB** |

Lo stock **non sarà più avviabile** come sistema, perché rootfs0 viene sovrascritto. Restano però il suo kernel e la sua recovery USB.

### Variante scartata per ora

Un Device Tree con UBI confinata a rootfs1 conserverebbe anche rootfs0 e permetterebbe di riavviare lo stock con un flag. Richiede però una patch al DTS, una gestione dei sysupgrade su misura e nessuno l'ha mai provata. Il vantaggio è marginale, perché il ritorno allo stock è già garantito dalla recovery USB. La teniamo come alternativa se il punto 3.A3 smentisse le ipotesi.

### Immagini (build del 10/11/2026 20:11 con Wi-Fi del laboratorio, `configs/build-2026-11-10-wifi.sha256sums`)

| File | Destinazione | SHA-256 |
| --- | --- | --- |
| `openwrt-ramips-mt7620-xiaomi_miwifi-r3-squashfs-kernel1.bin` (2,62 MiB) | `kernel1` | `1a38c2e02d55c9c13869be7a584f6ef88444fa462f80a49133aab574adcbcdf4` (MD5 `40b6070da3ac5f70f3923ed9a9dd4a9b`) |
| `openwrt-ramips-mt7620-xiaomi_miwifi-r3-squashfs-rootfs0.bin` (4,75 MiB) | `rootfs0` | `d46a6a2bd5c381eac9a7a9f8b5b9f06a97e87800eb51da90dc4053677214ebc8` (MD5 `8ba5be646d74bb5023c53b3985453841`) |
| `...-squashfs-sysupgrade.bin` | aggiornamenti successivi da X-Wrt | `58f69e6154e64689a1a3edf7cec08fdcad035fa0b623b14e3bd30ee4782b5ba9` |

L'MD5 serve per il controllo sul router, dove `sha256sum` non esiste. Rispetto alla build delle 19:41 il kernel1 è identico; cambia solo il rootfs, per lo script Wi-Fi. Il manifest dei pacchetti è invariato.

Non si usano `factory.bin` (formato non accettato dal pannello Xiaomi) né `breed-factory.bin` (richiede il bootloader Breed, che non installiamo).

## 3. Fasi

### Fase A — preparazione, nessuna modifica al router

- [ ] **A1. Seconda copia del backup** su un supporto indipendente (chiavetta, disco esterno o NAS), poi verifica con `sha256sum -c`.
- [x] **A2. Firmware ufficiale R3 firmato**: scaricato `miwifi_r3_firmware_4accc_2.26.39.bin` (la versione installata) dal server OTA Xiaomi, salvato in `work/stock-firmware/` con hash in `configs/stock-firmware.sha256`. Verifiche: CRC dell'header valido; kernel identico byte per byte al kernel0 del backup; **firma RSA-2048/SHA-1 valida** con la chiave pubblica dello stock (lo stesso controllo della recovery); nessun `uboot.bin` all'interno. Evidenze in [evidence/2026-11-10-stock-firmware.json](evidence/2026-11-10-stock-firmware.json).
  - [ ] Resta da preparare la **chiavetta**: FAT32, una sola partizione, il file `.bin` nella radice. Va fatto di persona.
- [x] **A3. Verifiche in sola lettura sul router stock** (10/11/2026; `scripts/read_install_checks.sh` e `scripts/read_boot_logic.sh`; evidenze in [evidence/2026-11-10-install-readonly-checks.json](evidence/2026-11-10-install-readonly-checks.json)). Nessuna modifica al router.
  - **Flag:** a ogni avvio riuscito `/usr/sbin/boot_check` imposta `flag_last_success` all'indice del sistema avviato (0 = kernel0/rootfs0, 1 = kernel1/rootfs1) e azzera `flag_try_sys*_failed`. `flag_try_sysN_failed` viene messo a 1 dall'initramfs (rootfs non montabile) e da `key_services_boot_check` (servizi falliti). `flag_boot_rootfs` viene solo letto dagli script userspace: lo scrive il bootloader in base al sistema che avvia. Quindi **`flag_last_success=1` → il bootloader sceglie il System 2 (kernel1)**, coerente con la ricetta X-Wrt. La logica interna di U-Boot non è stata disassemblata: resta un'inferenza forte, non una prova.
  - **Reset:** GPIO 30, valore 1 a tasto rilasciato (premuto = 0, come atteso dalla recovery).
  - **Blocchi danneggiati:** 0 su rootfs0 e su overlay (UBI). rootfs1 non verificato perché lo stock non lo monta.
  - **Strumenti sul router:** `mtd` (con `write` e `verify`), `md5sum`, `nanddump`, `flash_erase`, `ubiformat`, `curl`, `wget`. **`sha256sum` assente**: sul router si verifica con MD5, sul PC con SHA-256.
  - **Spazio:** 59 MB liberi in `/tmp`, sufficienti per le due immagini (7,4 MB).
- [ ] **A4. Accesso al primo avvio senza cavo.** Il Wi-Fi di X-Wrt parte spento e il PC ha un solo cavo, quello di Internet e della VPN. Quindi:
  - [x] nell'immagine, `/etc/board.d/99-lab-wifi` (generato dal wrapper con SSID e password da `private/router_wifi.conf`) accende **solo la radio a 2,4 GHz** in WPA2, sulla rete `lan`, paese IT. Il dongle del PC va solo a 2,4 GHz;
  - [ ] sul PC, profilo `xwrt-lab` (dongle, 192.168.15.10/24, senza gateway né DNS, autoconnessione): **`sudo bash scripts/setup_pc_xwrt_network.sh`**. Da SSH polkit nega la creazione, quindi va lanciato da Francesco;
  - 192.168.15.0/24 non è in conflitto con le reti del PC (Docker compreso).
- [ ] **A5. Scheda finale** con immagini, hash, flag e comandi esatti, approvata da Francesco.

### Fase B — installazione (solo dopo il via libera)

Da eseguire come root sullo stock tramite lo stesso canale già dimostrato, con uno script revisionato:

```sh
# 1. trasferimento in /tmp e verifica hash sul router
cd /tmp && <download di kernel1.bin e rootfs0.bin dal PC>
md5sum kernel1.bin rootfs0.bin       # sha256sum non esiste sullo stock: confronto MD5 col PC

# 2. flag (gli unici cambi NVRAM)
nvram set flag_last_success=1        # avvio dal System 2 = kernel1
nvram set boot_wait=on               # finestra del menu U-Boot se un giorno servirà la seriale
nvram set uart_en=1                  # console seriale attiva per un recupero d'emergenza
nvram commit

# 3. scrittura
mtd write kernel1.bin kernel1
mtd write rootfs0.bin rootfs0

# 4. verifica di quanto scritto, poi riavvio
mtd verify kernel1.bin kernel1
mtd verify rootfs0.bin rootfs0
reboot
```

Lo script deve fermarsi senza scrivere se un hash non corrisponde.

### Fase C — primo avvio

- [ ] Attendere 3–5 minuti; `ping 192.168.15.1`; `ssh root@192.168.15.1` con la chiave.
- [ ] Controllare `dmesg`, `cat /proc/mtd`, `ubinfo -a`, `fw_printenv`, Wi-Fi (mt76x2), USB e porte Ethernet.
- [ ] Impostare la password root per la console e verificare che SSH resti accessibile solo con la chiave.
- [ ] Salvare il backup della configurazione X-Wrt (`sysupgrade -b`) sul PC.
- [ ] Configurare e misurare WireGuard.

## 4. Matrice di recupero

| Scenario | Come si recupera | Serve la seriale? |
| --- | --- | --- |
| X-Wrt si avvia ma configurazione o rete sono sbagliate | Failsafe OpenWrt (tasto reset durante l'avvio, poi 192.168.15.1) oppure `firstboot`; poi SSH | No |
| Voglio tornare allo stock | Da X-Wrt: `fw_setenv flag_last_success 0`, `fw_setenv flag_try_sys1_failed 0`, `fw_setenv flag_try_sys2_failed 0`. Riavvio **tenendo premuto reset** con la chiavetta A2 inserita: il kernel0 stock entra in recovery e riscrive tutto | No |
| Il bootloader avvia per errore kernel0 | L'initramfs stock non trova il suo rootfs, imposta `flag_try_sys1_failed=1` e riavvia; il bootloader dovrebbe passare al System 2 (kernel1). Con reset premuto e chiavetta si torna allo stock | No |
| kernel1 X-Wrt corrotto (CRC errato) | Il bootloader verifica il CRC e dovrebbe ripiegare sul kernel0 stock, quindi recovery USB | Probabilmente no |
| **kernel1 X-Wrt con CRC valido ma che non arriva al sistema** (panic, blocco) | Il bootloader continua ad avviarlo: non c'è un ripiego automatico noto | **Sì**: menu U-Boot via UART (attivato in B2) e TFTP |
| Bootloader danneggiato | Non lo tocchiamo; servirebbe un programmatore NAND | Oltre la seriale |

**Rischio residuo da accettare consapevolmente:** se il nuovo kernel non si avvia, il recupero richiede la console seriale. Serve un adattatore USB-TTL a 3,3 V (pochi euro) e l'apertura del case per accedere ai pad UART sulla scheda. Non possiamo provare l'immagine in RAM prima del flash: kexec non è implementato nello stock e il TFTP richiede la seriale. Il rischio è contenuto da tre fatti: profilo e driver sono quelli usati dalla comunità X-Wrt per l'R3; header e CRC del kernel1 sono verificati; il kernel occupa 2,62 MiB su 4. Avere l'adattatore in casa prima del flash è un'assicurazione economica, anche se non si prevede di usarlo.

## 5. Punti aperti

- Semantica di `flag_last_success` nel bootloader: confermata indirettamente dagli script stock (A3). Una prova diretta richiederebbe il disassemblaggio di U-Boot o la seriale.
- Comportamento di UBI al primo avvio sull'area che contiene ancora i vecchi dati stock (rootfs1, overlay): la ricetta della comunità funziona così, ma registreremo il `dmesg` del primo avvio.
- Indirizzo del failsafe X-Wrt: **192.168.15.1** (`CONFIG_TARGET_PREINIT_IP` nella configurazione della build), lo stesso della LAN.
