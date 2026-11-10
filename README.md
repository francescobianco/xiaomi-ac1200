# Xiaomi Mi Router 3 — laboratorio Linux e VPN

**Per riprendere il lavoro: leggere [TODO.md](TODO.md).**

Progetto per recuperare lo Xiaomi identificato negli appunti come **Mi Router 3 (R3)**, installare un sistema Linux controllabile e studiare un percorso di aggiornamento sostenibile.

Il nome della cartella conserva la descrizione iniziale «AC1200», che identifica una classe Wi-Fi e non il modello hardware.

- [Dossier: dispositivo, stato delle prove e fonti](docs/DOSSIER.md)
- [Piano operativo e criteri di avanzamento](docs/PIANO.md)
- [Registro delle sessioni e dati da raccogliere](docs/REGISTRO.md)
- [Verifica diretta e analisi della via di accesso](docs/ACCESSO.md)
- [Build moderna X-Wrt e sorgenti fissati](docs/BUILD.md)
- [Analisi del recupero e dei layout](docs/RECUPERO.md)

**Stato al 10 novembre 2026:** configurazione stock completata e accesso root tramite API dimostrato, senza seriale. Copia logica con ECC della NAND (128 MiB) acquisita e verificata; lettura raw/OOB fallita. SSH non installato; firmware, bootloader e parametri NVRAM non modificati dalla procedura di accesso. Internet del PC resta sul cavo.

Base candidata scelta: X-Wrt, kernel 6.18.60; prima compilazione locale terminata con errore negli strumenti host ncurses/util-linux. Prossimo traguardo: verificare gli artefatti e predisporre il recupero. Nessuna immagine ancora selezionata o installata. Credenziali in `private/`, dump in `backups/`, entrambi esclusi da Git.
