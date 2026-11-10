# Base di compilazione R3

## Scelta corrente

Usiamo come candidata **X-Wrt**, revisione `61de4809b444b7a3d3c0a9cc27c1e0d6702572e4`, kernel previsto **6.18.60**, target `ramips/mt7620`, profilo `xiaomi_miwifi-r3`.

Il clone Git effettuato il 10 novembre 2026 contiene effettivamente:

- [Profilo immagini R3](https://github.com/x-wrt/x-wrt/blob/61de4809b444b7a3d3c0a9cc27c1e0d6702572e4/target/linux/ramips/image/mt7620.mk).
- [Device Tree R3](https://github.com/x-wrt/x-wrt/blob/61de4809b444b7a3d3c0a9cc27c1e0d6702572e4/target/linux/ramips/dts/mt7620a_xiaomi_miwifi-r3.dts).
- [Driver NAND MT7620](https://github.com/x-wrt/x-wrt/blob/61de4809b444b7a3d3c0a9cc27c1e0d6702572e4/target/linux/ramips/files/drivers/mtd/maps/ralink_nand.c), con adattamenti per API recenti.
- Patch di integrazione per kernel 6.18 e gestione upgrade R3.

Questo corregge la prima ricognizione via pagina web, che non mostrava il profilo. Fa fede il checkout locale a revisione fissata, con hash dei file nel lock. La presenza dei sorgenti non equivale a una prova su hardware.

## Materiale riproducibile

- [Seed minimo](../configs/r3-lab.seed): target R3, initramfs e filesystem SquashFS, senza LuCI e PPP.
- [Configurazione espansa](../configs/r3-lab.expanded.config): configurazione realmente generata da Kconfig.
- [Lock sorgenti](../configs/sources.lock.json): revisione, versione kernel, hash configurazione e file rilevanti.
- [Wrapper build](../scripts/build_lab.sh): percorsi per le dipendenze host locali, PATH ripulito da Homebrew, flag host come override make.
- [Checksum](../configs/build-2026-11-10.sha256sums) e [manifest](../configs/build-2026-11-10.manifest) della prima build riuscita.

Nessun feed esterno è stato installato per questa prima build minima. Il parser segnala dipendenze opzionali mancanti di pacchetti non selezionati; la compilazione effettiva determinerà se la configurazione scelta ne richiede altre.

I sorgenti sono in `work/x-wrt/`, esclusi da Git. L'host è Ubuntu 24.04 amd64. Per ncurses è stato estratto localmente il pacchetto ufficiale Ubuntu `libncurses-dev` versione `6.4+20240113-1ubuntu2.2`, senza installazione di sistema. Il wrapper limita i percorsi extra ai compilatori host; CPATH viene usato soltanto per configurazione e prerequisiti.

## Comandi della sessione

```bash
cp configs/r3-lab.seed work/x-wrt/.config
bash scripts/build_lab.sh defconfig
bash scripts/build_lab.sh -j8 download > work/download.log 2>&1
bash scripts/build_lab.sh -j8 > work/build.log 2>&1
```

Ripetere la copia del seed soltanto per ricreare intenzionalmente la configurazione. I comandi lavorano sul PC e non installano immagini sul router.

Output atteso: `work/x-wrt/bin/targets/ramips/mt7620/`. Prima dell'uso verificare profilo, checksum, dimensioni, header, limiti dei kernel da 4 MiB e metadati. `factory.bin`, `breed-factory.bin`, `sysupgrade.bin` e immagini separate hanno destinatari differenti: il nome «factory» non garantisce accettazione da parte del pannello Xiaomi stock.

L'initramfs è un artefatto per prove di avvio; sul nostro firmware stock kexec non è implementato. Non abbiamo ancora dimostrato un metodo per avviarlo in RAM senza seriale.


## Esito della prima build

La prima make completa è terminata con exit code 2: errore `tools/util-linux`, `cur_term` non dichiarato. Il wrapper esporta flag host che `rules.mk` riassegna; il configure Meson ha inoltre rilevato percorsi ncurses Homebrew.

## Fix e build riuscita

Causa effettiva: Meson non trovava ncurses con pkg-config e ripiegava su `ncursesw6-config` di Homebrew, presente nel PATH dell'utente. Fix riproducibile in `scripts/build_lab.sh`:

- rimuove le voci linuxbrew dal PATH e azzera HOMEBREW_*, PKG_CONFIG_PATH/LIBDIR, CPATH, C_INCLUDE_PATH e LIBRARY_PATH;
- passa `HOST_EXTRA_CFLAGS=-I<sysroot>/usr/include` e `HOST_EXTRA_LDFLAGS=-L<sysroot>/usr/lib/x86_64-linux-gnu` come override da riga di comando di make. rules.mk riassegna le variabili esportate, mentre gli override valgono anche nei sub-make. Riguardano solo gli strumenti host, non il cross compiler MIPS;
- per `prereq`/`defconfig`/`oldconfig`/`menuconfig` usa CPATH/LIBRARY_PATH, perché quei controlli non leggono HOST_EXTRA_*.

Verifica: `tools/util-linux/clean` e `compile -j1 V=s` riusciti. Meson trova curses 6.4 del sysroot Ubuntu (`HAVE_NCURSES_H`, `HAVE_TERM_H`) e non compaiono percorsi linuxbrew.

Build completa ripresa: **exit 0** il 10 novembre 2026 alle 19:29, circa 16 minuti con `-j8` (riusando gli strumenti host già compilati). Configurazione identica all'hash del lock.

| Artefatto | Esito |
|---|---|
| `sha256sums` | tutti OK |
| `squashfs-kernel1.bin` | uImage Linux 6.18.60, 2,62 MiB (entra nello slot da 4 MiB), CRC header e dati OK |
| `initramfs-kernel.bin` | uImage di 6,06 MiB, CRC OK. Solo avvio da RAM, non entra in uno slot |
| `squashfs-sysupgrade.bin` | tar con `CONTROL`, `kernel`, `root` |
| `squashfs-factory.bin`, `breed-factory.bin`, `rootfs0.bin` | prodotte, compatibilità non verificata |

Il manifest elenca 107 pacchetti: dropbear, wpad-basic-mbedtls, mt76x2, USB2. LuCI e WireGuard non sono inclusi. Dettagli in [evidence/2026-11-10-build-artifacts.json](evidence/2026-11-10-build-artifacts.json). **Nessuna immagine è stata installata**: prima servono le aggiunte (WireGuard, accesso SSH con chiave) e il piano di installazione e recupero.
