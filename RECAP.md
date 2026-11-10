# RECAP — ripresa sessione da remoto (10 novembre 2026, aggiornato 19:38)

> **AGGIORNAMENTO 19:45 — SECONDA BUILD RIUSCITA (exit 0 alle 19:41) e verificata; documentazione, commit e push fatti.**
> **19:55 — Piano di installazione e recupero scritto in `docs/INSTALLAZIONE.md` (proposta).** Nessun flash eseguito.
> **20:05 — A3 fatta (sola lettura sul router):** semantica dei flag confermata dagli script stock; dettagli in `docs/INSTALLAZIONE.md`. Restano A1, A2, A4, A5.
> **20:15 — A2 e A4 fatte per la parte possibile da remoto.** Firmware stock 2.26.39 scaricato e verificato (firma RSA valida). Immagine ricompilata con il Wi-Fi a 2,4 GHz acceso (`R3-XWrt-Lab`). Restano da fare di persona o con sudo: copia del backup su un supporto esterno, chiavetta FAT32 con il firmware, approvazione della scheda.
> **20:20 — profilo `xwrt-lab` creato da Francesco e verificato: A4 completata.**
> **20:45 — FLASH ESEGUITO (fase B), su richiesta di Francesco.** kernel1 e rootfs0 scritti e verificati, flag impostati, riavvio. **X-Wrt si avvia**: risponde su 192.168.144.152 (WAN sulla LAN dell'ufficio, hostname `OpenWrt`). Il Wi-Fi `R3-XWrt-Lab` NON compare e il lato WAN è chiuso: serve un accesso dalla LAN (cavo sulla porta LAN) per diagnosticare. Il dongle del PC si è ricollegato da solo al Wi-Fi del Fritz (profilo salvato). Dettagli in docs/INSTALLAZIONE.md §6.
> **21:15 — Fine sessione. Piano per domani in `TODO.md`, sezione «Domani (11/11/2026)»:** 1) WireGuard server, 2) installazione a casa con la Iliadbox, 3) btedge sul router (va riscritto `bluez.py` per dbus-fast).
> **21:05 — Password root impostata, SSH solo con chiave verificato, backup della configurazione in `backups/xwrt-config/`.** Prossimo: WireGuard (server o client?).
> **21:00 — ACCESSO RIUSCITO SENZA CAVO.** Il Wi-Fi `R3-XWrt-Lab` funzionava: Claude non poteva scansionare da SSH (polkit). Con `sudo nmcli con up xwrt-lab` il dongle è su 192.168.15.10; `ssh root@192.168.15.1` funziona; diagnosi tutta in ordine. Il piano del cavo grigio NON serve più. Prossimo: password root, `sysupgrade -b`, WireGuard.
> ~~PROSSIMO PASSO (11/11 in ufficio):~~ Francesco collega un cavo a una **porta LAN grigia** del router (la blu è la WAN, già sulla LAN dell'ufficio: lasciarla). MAI collegare una porta LAN grigia alla rete dell'ufficio (X-Wrt è server DHCP).
> - Se il cavo grigio va al PC al posto di `eno1`: il PC prende 192.168.15.x via DHCP (si perde la VPN remota finché dura). Poi `bash scripts/diag_xwrt.sh` → rapporto in `private/xwrt-diag-*.txt` (sola lettura).
> - Da diagnosticare: perché la radio a 2,4 GHz / `R3-XWrt-Lab` non è partita (board.json → wlan, `uci show wireless`, `wifi status`, dmesg rt2800).
> - Poi: password root, `sysupgrade -b`, WireGuard. Router verificabile da remoto con `ping 192.168.144.152`.
> **20:25 — A1 completata:** backup e firmware copiati sul PC di casa di Francesco, SHA-256 OK. Restano la chiavetta FAT32 con il firmware (A2) e l'approvazione della scheda (A5).
>
> Storico della seconda build (WireGuard + chiave SSH + Image Builder):
> Decisione di Francesco: aggiungere WireGuard, accesso SSH con chiave e Image Builder; LuCI per ora no.
> - Avviata alle 19:36 **staccata da Claude** (`setsid nohup`, `-j12`): sopravvive alla chiusura delle sessioni.
>   Log: `work/build-wg.log`; a fine build l'ultima riga è `exit=N`. Controllo: `pgrep -af 'make -j12'`.
> - Seed aggiornato (`kmod-wireguard`, `wireguard-tools`, `CONFIG_IB=y`); config espansa e hash nel lock aggiornati.
>   La differenza rispetto alla build precedente comprende solo WireGuard, le sue dipendenze crypto/udptunnel e IB.
> - Overlay immagine: `configs/files/etc/uci-defaults/90-lab-ssh` (dropbear senza password, solo LAN) e
>   la chiave pubblica `private/router_authorized_keys` (copia di `~/.ssh/id_rsa.pub`, RSA 3072, fuori da Git).
>   `scripts/build_lab.sh` ricrea `work/x-wrt/files/` a ogni build e si rifiuta di partire senza chiave.
> - LAN predefinita di X-Wrt: **192.168.15.1**. **Decisione di Francesco: mantenerla** (organizzazione degli indirizzi), non cambiarla.
> - Dopo la build: verificare immagini, WireGuard nel manifest, presenza di authorized_keys e uci-defaults nel
>   rootfs e dell'Image Builder; poi documentazione, commit e push. Nessun flash.

> **AGGIORNAMENTO 19:31 — BUILD COMPLETATA CON SUCCESSO (`exit=0`, finita alle 19:29).**
> La sessione dell'ufficio non ha più make attive: l'istanza di casa può prendere in mano tutto.
> Le sezioni sotto su "build in corso" sono storiche. Vedi "Esito build" più in basso.

Leggere prima questo file, poi `TODO.md` (passaggio di consegne completo e regole).

## Contesto di questa sessione: LEGGERE SUBITO

- Francesco è **a casa** e lavora su questo PC (quello dell'ufficio) **via VPN e SSH**.
  Ha aperto questa sessione con `claude --continue`: è una **seconda istanza** che ha
  ricaricato la conversazione.
- **In parallelo è ancora aperta la sessione originale** sul terminale dell'ufficio. È lei che
  ha lanciato la build ed è la madre del processo `make`. Le due istanze condividono lo
  stesso albero di lavoro.
- Conseguenze per questa istanza:
  - **Non avviare un secondo `make` nella stessa directory finché quello originale è attivo**:
    due build concorrenti su `work/x-wrt` corrompono build_dir/staging_dir. Controllare
    sempre prima con `pgrep -af 'make.*-j8'`.
  - **Non terminare** la make, né i processi o la sessione dell'altra istanza.
  - Questa istanza **non riceve la notifica di fine build**: lo stato si legge dal log
    (vedi sotto). Non usare sleep per attendere: chiedere a Francesco o ricontrollare quando lo chiede.
  - Solo una shell SSH: niente GUI, browser o IDE su questo PC.
  - Le modifiche ai file sono visibili a entrambe le istanze. Prima di modificare un file
    rileggerlo, e non fare commit in contemporanea con l'altra istanza.
- Quando la build originale è **terminata** (riga `exit=N` nel log, nessuna make attiva),
  questa istanza può prendere in mano tutto il lavoro, rilanci compresi.

## Dove eravamo

1. **Risolto l'errore `tools/util-linux`** della prima build.
   - Causa: Meson non trovava ncurses con pkg-config e ripiegava su `ncursesw6-config`
     di **Homebrew** (`/home/linuxbrew/...`), mescolando header e librerie estranei
     (`cur_term` undeclared in `lib/colors.c`).
   - Fix in `scripts/build_lab.sh`: rimuove linuxbrew dal PATH, azzera
     HOMEBREW_*/PKG_CONFIG_*/CPATH/LIBRARY_PATH e passa `HOST_EXTRA_CFLAGS`/`HOST_EXTRA_LDFLAGS`
     come **override make da riga di comando** (rules.mk riassegna quelli esportati).
     Valgono solo per gli strumenti host, non per il cross compiler MIPS.
   - Verificato: `tools/util-linux/clean` + `compile -j1 V=s` riusciti
     (`work/util-linux-fix.log`), curses 6.4 dal sysroot Ubuntu, zero percorsi linuxbrew.

2. **Build completa ripresa** alle ~19:13 con:
   ```bash
   bash scripts/build_lab.sh -j8 > work/build-resume.log 2>&1; echo "exit=$?" >> work/build-resume.log
   ```
   - È stata lanciata come processo in background della sessione Claude sull'ufficio:
     se quella sessione viene chiusa, la build muore.
   - Alle 19:23: tools host e toolchain (gcc 14.4, musl) completati, in corso `target/linux` (kernel 6.18).
   - Stima di fine: **circa 20:00–20:20**, se non emergono altri errori.

## Esito build (controlli eseguiti alle 19:30)

- Output in `work/x-wrt/bin/targets/ramips/mt7620/`, versione `r0-61de480`, kernel **Linux 6.18.60**.
- `sha256sum -c sha256sums`: tutti OK.
- `squashfs-kernel1.bin`: uImage di 2,62 MiB (sotto i 4 MiB dello slot), CRC header e dati OK, load/ep 0x80000000.
- `initramfs-kernel.bin`: uImage di 6,06 MiB, CRC OK. Supera i 4 MiB: va bene solo per avvio da RAM (TFTP), non per lo slot kernel.
- `squashfs-sysupgrade.bin`: tar con `CONTROL`, `kernel`, `root`. Ci sono anche `squashfs-factory.bin`, `breed-factory.bin` e `rootfs0.bin`.
- Manifest con 107 pacchetti: dropbear, wpad-basic-mbedtls, mt76x2, USB2. **Mancano LuCI e WireGuard** (build minima).
- **Nessuna immagine è stata flashata né proposta per il flash.**

### Prossimi passi proposti (da concordare con Francesco)

1. ~~Aggiornare documentazione, evidenze, commit e push~~ — **FATTO alle 19:40** (commit su main).
2. Decidere le aggiunte all'immagine (WireGuard, accesso SSH sicuro con chiave, eventuale LuCI) e se
   attivare Image Builder / ccache.
3. Studiare con i dati reali il piano di installazione e di recupero: quale immagine usare, quale
   layout, cosa succede al fallback stock (vedi TODO.md, sezione Recupero). Va fatto prima di qualsiasi flash.

## Cosa fare appena ripresa la sessione (valido se la build non fosse finita)

1. Controllare la build:
   ```bash
   tail -5 work/build-resume.log                      # ultima riga exit=N a build finita
   grep -E '^ make\[' work/build-resume.log | tail -3 # fase corrente
   pgrep -af 'make.*-j8' || echo "nessuna make attiva"
   ```
   - Se non c'è `exit=` e nessuna make è attiva, la build è stata interrotta (sessione chiusa,
     sospensione): rilanciare il comando sopra. Riparte da dove era (marcatori `.built`/stamp),
     non da zero.
2. **Se `exit` è diverso da 0**: cercare `ERROR:` nel log, diagnosticare il pacchetto con
   `bash scripts/build_lab.sh <pacchetto>/compile -j1 V=s`, correggere in modo riproducibile
   (wrapper/config, non a mano in build_dir) e riprendere la build.
3. **Se `exit=0`**: controllare gli artefatti in `work/x-wrt/bin/targets/ramips/mt7620/`
   (immagini R3, kernel ≤ 4 MiB, CRC uImage, sha256sums, manifest). **Non flashare**: prima
   piano di installazione e recupero concordati con Francesco (vedi TODO.md, sezione Recupero).
4. Aggiornare `TODO.md`, `docs/BUILD.md`, `docs/REGISTRO.md`, `README.md` con l'esito reale,
   poi commit e push (credenziali e dump restano fuori da Git).

## Modifiche non ancora committate

- `scripts/build_lab.sh` (fix Homebrew/override make)
- `TODO.md` (due checkbox della build spuntati)
- `RECAP.md` (questo file)

## Proposte in sospeso (da decidere con Francesco, dopo la prima build riuscita)

- Attivare **Image Builder** (`CONFIG_IB`) per generare nuove immagini (WireGuard, configurazioni)
  in pochi minuti senza ricompilare; eventualmente **SDK** e **ccache**.
  Cambia la configurazione: aggiornare `configs/` e `sources.lock.json`.
- Usare `-j12` (il PC ha 12 core) nelle build future.
- Lanciare le prossime build lunghe dentro `tmux` o con `setsid nohup`, così sopravvivono
  alla chiusura della sessione.

## Promemoria

- Ambiente: build solo locale, nessuna comunicazione con il router in questa fase.
- Il PC non deve andare in sospensione durante la build.
