# Registro del laboratorio

## 2026-11-10 — dossier iniziale

- Ricevuta la trascrizione della sessione precedente.
- Creati dossier, piano operativo e questo registro.
- Consultati sorgenti pubblici: individuata anche una patch comunitaria per OpenWrt 22.03.
- Nessuna operazione di rete o scrittura sul router eseguita in questa sessione.
- Repository iniziale quasi vuoto; directory `.idea/` preesistente non modificata.

## Dati ancora da acquisire

| Dato | Valore verificato / riferimento locale |
| --- | --- |
| Modello da etichetta e revisione | Da acquisire |
| Firmware e stato configurazione | Verificato via init_info: R3, 2.26.39, CN, inited=0; vedere evidence/2026-11-10-probe.json |
| SoC, RAM e chip NAND | Da acquisire |
| Mappa MTD, geometria NAND, ECC | Da acquisire |
| Bootloader e recovery | Da acquisire |
| Metodo di accesso e revisione strumento | Da scegliere |
| Inventario backup e checksum | Da creare |
| Base firmware, commit, feeds | Da scegliere |
| Ruolo VPN e prestazioni richieste | Da definire |

## 2026-11-10 — configurazione e accesso software, senza seriale

- Francesco ha autorizzato di proseguire senza seriale per adesso.
- Completata la configurazione iniziale tramite il flusso del pannello stock: `set_router_normal` ha restituito `code=0`.
- Creata rete protetta `Xiaomi-R3-Lab` e password distinte casuali di 24 caratteri per Wi-Fi e amministrazione; conservate in `private/credentials.json`, directory 0700 e file 0600, esclusi da Git.
- Creato profilo NetworkManager `xiaomi-lab`, autoconnect disabilitato, nessuna route predefinita o DNS automatico, IPv6 disabilitato sul solo profilo di laboratorio. Riconnessione riuscita e login con nuova password verificato.
- Adattata la via `c_upload` / `netspeed` dei progetti xmir-patcher e OpenWRTInvasion. Il ripristino configurazione restituisce 1629, ma una prova successiva ha dimostrato l'esecuzione dello script temporaneo: callback `uid=0` e inventario ricevuto.
- Il primo tentativo con XML compatto non aveva prodotto callback; mantenendo la struttura multilinea del riferimento e lo script in background la prova è riuscita. La causa precisa non è isolata, perché sono cambiati anche metadati tar e modalità di esecuzione.
- Confermati kernel stock 2.6.36, MemTotal 124772 KiB, NAND 128 MiB, eraseblock 128 KiB, pagina 2048 byte e OOB 64 byte. [Inventario pubblico depurato](evidence/2026-11-10-root-inventory.json).
- Non installati SSH/Telnet, non modificata la password root, non eseguiti comandi di modifica NVRAM o bootloader. L'accesso attuale è esecuzione root tramite API amministrativa, non una shell SSH permanente.
- Acquisita tutta la NAND con ECC: 32 blocchi da 4 MiB (134217728 byte). Dimensioni e MD5 remoto/locali verificati per tutti; SHA-256 locali nel manifest. Dump combinato in `backups/2026-11-10/full-ecc.bin`.
- Acquisita una seconda lettura dei primi 4 MiB: Bootloader, Config, Bdata e Factory risultano identici byte per byte.
- Raw/OOB fallito durante il primo blocco: nanddump restituisce errore I/O (`mtd_read`). Copia raw non disponibile; nessun file parziale conteggiato come backup riuscito.
- La verifica locale restituisce un esito incompleto per il raw e conferma separatamente la validità del backup logico ECC. Ripristino e seconda copia su supporto indipendente restano da predisporre.
- Ripuliti i file temporanei introdotti sul router; rapporto di cleanup ricevuto via esecuzione root. Nessun server SSH installato; il server di raccolta sul PC è stato chiuso al termine.

## 2026-11-10 — prima verifica diretta

- Dongle già collegato a `xiaomi-setup`, indirizzo 192.168.31.222/24; route predefinita IPv4 sul cavo Ethernet. Nessuna modifica a NetworkManager eseguita.
- Confermati dal router R3 e firmware 2.26.39; configurazione iniziale ancora da completare.
- Porte TCP 22, 23 e 122: connessione rifiutata.
- Salvata evidenza depurata da seriali e identificativi unici; aggiunta sonda ripetibile in `scripts/probe_router.py`.
- Scaricati ed esaminati, senza eseguirli, sorgenti xmir-patcher a revisione fissata. [Risultati e modifiche previste](ACCESSO.md).
- Chiesta disponibilità di adattatore UART per definire il recupero.
- Nessuna autenticazione, configurazione, modifica NVRAM, installazione o acquisizione flash eseguita.

## Modello per le sessioni successive

```text
Data:
Obiettivo:
Stato iniziale e collegamenti:
Fonti e revisioni strumenti:
Operazioni eseguite e modifiche persistenti:
Evidenze / log locali depurati:
Esito e problemi:
Ripristino disponibile:
Prossimo passo e condizioni per procedere:
```

Registrare solo risultati osservati. Tenere credenziali, token, chiavi VPN, dump e dati di fabbrica fuori dai documenti versionati; usare riferimenti locali ai file riservati.


## 2026-11-10 — analisi offline e build moderna

- Verificati hash del backup combinato e CRC di header/payload dei due kernel stock, entrambi validi. Bootloader identificato dalle stringhe come U-Boot 1.1.3 del 12 aprile 2016.
- Clonati in `work/` sorgenti di riferimento storici e X-Wrt attuale. Il checkout X-Wrt conferma supporto R3 e driver NAND per 6.18: corretta la precedente ricognizione web incompleta.
- Scelta come candidata la revisione `61de4809b444b7a3d3c0a9cc27c1e0d6702572e4`, kernel 6.18.60. Salvati seed, configurazione espansa, lock e inventario checksum degli archivi scaricati.
- Prerequisiti superati usando header ncurses estratti da un pacchetto Ubuntu nella cartella di lavoro: sudo richiedeva password e non è stato usato per installare pacchetti di sistema.
- Download della configurazione minima completato; avviata compilazione locale con 8 processi. Log: `work/download.log` e `work/build.log`.
- Letti senza modificarli i flag di avvio; confermato stock attivo nello slot 0. `sys_kexec_load` coincide con `sys_ni_syscall`: kexec non implementato dal kernel corrente.
- Il Device Tree standard X-Wrt unifica rootfs0, rootfs1 e overlay in una UBI da 118 MiB. Questa trasformazione richiede un piano di recupero: conservare kernel0 non conserva da solo il sistema stock.
- Nessun riavvio, cambio NVRAM, flash o sostituzione bootloader eseguito in questa fase.


## Passaggio di consegne e pubblicazione richiesta

- Prima compilazione completa terminata con exit code 2, errore host util-linux/ncurses (`cur_term` non dichiarato). Nessuna build completa lasciata attiva.
- Salvata diagnosi e sequenza di ripresa in `TODO.md`: gli export HOST_EXTRA_* del wrapper sono sovrascritti da rules.mk; il fix resta da applicare e verificare.
- Francesco ha richiesto di completare TODO.md e fare commit/push del materiale del progetto. Credenziali, dump, checkout/cache di lavoro e impostazioni IDE restano esclusi da Git.


## 2026-11-10 sera — fix util-linux e prima build riuscita

- Causa dell'errore: Meson usava `ncursesw6-config` di Homebrew dal PATH. Il wrapper ora ripulisce il PATH e passa i flag host come override make. util-linux è stato ricompilato da solo con log verboso (`work/util-linux-fix.log`).
- Build completa ripresa: exit 0 alle 19:29. Immagini R3 controllate: checksum OK, kernel1 di 2,62 MiB con CRC OK, initramfs di 6,06 MiB solo per avvio da RAM. 107 pacchetti, senza LuCI né WireGuard.
- Checksum e manifest copiati in `configs/`, evidenze in `docs/evidence/2026-11-10-build-artifacts.json`.
- Nessuna comunicazione con il router, nessun flash, riavvio o modifica NVRAM.
- Prossimo passo: decidere le aggiunte all'immagine e definire il piano di installazione e recupero.

## 2026-11-10 sera — build con WireGuard e SSH con chiave

- Decisioni di Francesco: WireGuard, chiave SSH e Image Builder sì; LuCI no per ora; LAN 192.168.15.1 da mantenere.
- Seed e lock aggiornati; overlay `configs/files/` e chiave da `private/` inseriti dal wrapper.
- Build `-j12` staccata dalla sessione: exit 0 alle 19:41. Immagini, rootfs e Image Builder verificati (evidenze in `docs/evidence/2026-11-10-build-wireguard.json`).
- Nessuna comunicazione con il router, nessun flash.

## 2026-11-10 sera — piano di installazione e recupero

- Analisi offline del backup: il bootloader offre solo il menu TFTP via seriale. La recovery USB di Xiaomi sta nell'initramfs dei kernel stock (reset all'avvio o chiavetta `miusbkit`, firmware firmato RSA) e riscrive tutte le partizioni di sistema.
- Config è un ambiente U-Boot con CRC valido; `uboot-envtools` di X-Wrt lo gestisce su mtd1.
- Piano proposto in `docs/INSTALLAZIONE.md`: kernel1 + rootfs0, kernel0 stock preservato come via di recupero. Rischio residuo: un kernel che non si avvia richiede la seriale.
- Tentata l'installazione di ubi_reader in un ambiente isolato per leggere gli script OTA dal backup: bloccata dal classificatore dei permessi. Verifica spostata in A3 (lettura sul router).
- Nessuna comunicazione con il router.

## 2026-11-10 sera — verifiche in sola lettura per l'installazione (A3)

- Eseguiti come root sullo stock due script di sola lettura (`read_install_checks.sh`, `read_boot_logic.sh`). Rapporti integrali in `private/install-checks.txt` e `private/boot-logic.txt`, sintesi in `docs/evidence/2026-11-10-install-readonly-checks.json`.
- `boot_check` imposta `flag_last_success` all'indice del sistema avviato; `flag_boot_rootfs` lo scrive solo il bootloader. Ne segue che `flag_last_success=1` seleziona kernel1.
- Reset su GPIO 30; 0 blocchi danneggiati su rootfs0 e overlay; `sha256sum` assente (si useranno `md5sum` e `mtd verify`).
- Nessun nvram set/commit, nessuna scrittura mtd, nessun riavvio.

## 2026-11-10 sera — firmware stock per la recovery e Wi-Fi nell'immagine

- Scaricato il firmware ufficiale `miwifi_r3_firmware_4accc_2.26.39.bin` dal server OTA Xiaomi: firma RSA valida con la chiave dello stock, kernel identico al kernel0 del backup, nessun bootloader dentro. File in `work/stock-firmware/`, hash in `configs/stock-firmware.sha256`, evidenze in `docs/evidence/2026-11-10-stock-firmware.json`.
- L'API del router per gli aggiornamenti non dava link (il router non ha WAN); il nome del file viene da un elenco pubblico dei link OTA ufficiali.
- Aggiunta all'immagine la radio a 2,4 GHz accesa in WPA2 al primo avvio, per raggiungere il router dal dongle. Terza build riuscita e verificata.
- Profilo NetworkManager `xwrt-lab`: polkit nega la creazione da SSH, preparato `scripts/setup_pc_xwrt_network.sh` da lanciare con sudo.
- Nessuna modifica al router.

## 2026-11-10 sera — seconda copia del backup (A1)

- Ricontrollati gli hash locali del backup NAND e del firmware stock, poi creato il pacchetto `work/a1-export/xiaomi-r3-backup-2026-11-10.tar` (SHA-256 `83c95be1…4ca3`).
- Francesco l'ha copiato con rsync, via VPN, sul suo PC di casa e l'ha verificato con `sha256sum -c`: OK.
- NAS dell'ufficio (Synology .88, Fritz .1): accesso negato senza credenziali, copia rimandata.

## 2026-11-10 sera — flash di X-Wrt (fase B)

- Su richiesta esplicita di Francesco, flash da remoto senza attendere la chiavetta. Scritture di kernel1 e rootfs0 verificate (`Success`), flag impostati, riavvio alle 20:32.
- X-Wrt si avvia: WAN su 192.168.144.152 (`OpenWrt.fritz.box`). Wi-Fi non visibile, accesso solo dalla LAN.
- Il dongle del PC è passato da solo al Wi-Fi del Fritz dell'ufficio (profilo già salvato).

## 2026-11-10 21:00 — primo accesso a X-Wrt

- Errore di diagnosi corretto: il Wi-Fi c'era, mancava solo la scansione (polkit nega a Claude da SSH). Francesco ha attivato `xwrt-lab` con sudo.
- SSH con chiave su 192.168.15.1 riuscito; diagnosi in sola lettura tutta in ordine; il bootloader ha impostato `flag_boot_rootfs=1`.
