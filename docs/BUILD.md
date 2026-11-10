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
- [Wrapper build](../scripts/build_lab.sh): percorsi per le dipendenze host locali.

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

La prima make completa è terminata con exit code 2: errore `tools/util-linux`, `cur_term` non dichiarato. Non è ancora disponibile un'immagine verificata per l'installazione. Il wrapper esporta flag host che `rules.mk` riassegna; il configure Meson ha inoltre rilevato percorsi ncurses Homebrew. Il fix non è stato ancora applicato. Diagnosi e sequenza di ripresa dettagliate in [TODO.md](../TODO.md).
