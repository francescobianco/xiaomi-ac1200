# Piano operativo

Stato attuale: configurazione iniziale completata, esecuzione root tramite API dimostrata e backup logico ECC della NAND verificato. Raw/OOB fallito e ripristino non ancora validato. Francesco ha autorizzato di procedere senza seriale per adesso. Le fasi successive avanzano in base alle prove raccolte, senza una promessa di compatibilità o una data di completamento del porting.

## 1. Riconfermare dispositivo e collegamenti

- Raccogliere modello esatto dall'etichetta e revisione della scheda se accessibile; conservare seriale e MAC solo negli appunti locali necessari.
- Verificare rete e route attuali del PC prima di attivare il dongle. Mantenere Internet sul cavo; il profilo Xiaomi non deve fornire route predefinita o DNS al PC.
- Leggere stato della configurazione iniziale, modello e firmware dal pannello; salvare una risposta depurata da token e credenziali.
- Se serve completare la configurazione, usare una password robusta compatibile con lo strumento scelto, conservata fuori da Git. Documentare le modifiche e verificare le impostazioni di aggiornamento prima di proseguire.

**Uscita:** identità R3 riconfermata, firmware registrato, accesso locale funzionante e connettività del PC invariata. Se emerge un modello diverso, rivedere il piano.

## 2. Predisporre recupero e studiare l'accesso

- Individuare procedura di recovery stock, firmware originale corrispondente e condizioni necessarie per usarla.
- Valutare una console UART: adattatore USB-TTL con livelli logici 3,3 V, massa comune e piedinatura verificata. Non usare una porta RS-232 e non collegare il VCC dell'adattatore al router alimentato.
- Verificare boot log e capacità effettive del bootloader: seriale e TFTP sono possibilità da accertare, non recovery già dimostrati.
- Esaminare codice e compatibilità dello strumento di accesso prima di eseguirlo; fissarne la revisione e descrivere cosa modifica. Preferire una via documentata per quel firmware.

**Uscita:** percorso di accesso scelto con effetti noti; mezzi di recupero disponibili e limiti espliciti. Non sostituire il bootloader come primo esperimento.

## 3. Ottenere inventario e backup

Una volta ottenuta la shell, raccogliere prima informazioni: `uname -a`, `/proc/cpuinfo`, `/proc/meminfo`, `/proc/mtd`, log kernel e dati NAND/UBI disponibili. Leggere l'ambiente di avvio solo con strumenti e configurazione verificati.

- Documentare dimensioni, offset e funzione delle partizioni, incluse eventuali viste sovrapposte.
- Salvare bootloader, ambiente, dati di fabbrica/calibrazione e tutte le altre aree necessarie al ripristino, senza alterarle.
- Per NAND distinguere dump logico con correzione ECC e acquisizione raw con OOB/bad block. Un semplice file copiato da MTD non garantisce da solo un ripristino corretto.
- Registrare comando, versione dello strumento, geometria e opzioni usate. Verificare dimensioni e SHA-256 dei file trasferiti; eventuali differenze tra acquisizioni vanno spiegate anche in relazione a partizioni attive.
- Tenere almeno due copie, una fuori dal PC di lavoro. Preparare una mappa del ripristino senza eseguirlo per prova su dati unici.

**Uscita:** inventario reale e backup verificati, con una strategia di ripristino tecnicamente coerente. Password, chiavi, dump e calibrazioni non vanno pubblicati nel repository.

## 4. Scegliere la base e riprodurre una build

Due attività possono procedere separatamente: analisi dei sorgenti sul PC e inventario del router. Nessuna richiede di anticipare il flash.

1. Confrontare i port storici 21.02 e 22.03, cercare eventuali successori mantenuti e classificare le differenze rispetto a OpenWrt attuale.
2. Fissare repository e commit di base, feeds, toolchain, configurazione e patch. Scegliere esplicitamente bootloader e layout supportati.
3. Riprodurre una build di riferimento per comprendere la catena delle immagini. Una vecchia versione resta un riferimento di laboratorio.
4. Tentare il port su una release ancora mantenuta al momento della scelta; annotare errori di compilazione e incompatibilità delle API NAND.
5. Produrre manifest, checksum e istruzioni di build; ispezionare dimensioni, header e Device Tree prima di qualsiasi avvio.

**Uscita:** almeno una build ricostruibile e una valutazione documentata del costo del port moderno. Se il driver NAND blocca il lavoro, isolare quel problema e studiare un avvio senza rootfs NAND, se il bootloader lo permette.

## 5. Primo avvio sperimentale

Preferire initramfs caricato in RAM, se il bootloader reale lo supporta e se memoria e formato lo consentono. Verificare che anche gli script di avvio dell'immagine non scrivano automaticamente sulla flash.

Prima provare console, RAM ed Ethernet; poi NAND in lettura, USB e Wi-Fi. Salvare il log completo e controllare errori ECC, watchdog, riavvii e consumi di memoria. La scrittura NAND richiede una prova separata in una zona esplicitamente sacrificabile e compatibile con il layout, mai sui dati di fabbrica.

**Uscita:** avvio stabile, gestione Ethernet e lettura dello storage coerente. Se il boot in RAM non è possibile, documentare una procedura alternativa con recovery verificato prima di passare a un'installazione persistente.

## 6. Installazione persistente

Prima di eseguire scritture, preparare una scheda concreta con: hash dell'immagine, modello, layout originale e di destinazione, partizioni coinvolte, eventuali cambi all'ambiente, comandi specifici revisionati e recupero previsto. A quel punto concordare con Francesco l'esecuzione della procedura sul dispositivo.

Non forzare un'immagine che non supera i controlli di compatibilità. Conservare il bootloader originale finché non emerge una necessità dimostrata di cambiarlo.

**Uscita:** sistema avviabile dopo riavvio e spegnimento controllato, configurazione persistente, calibrazioni e MAC corretti, recovery ancora praticabile. Conservare log prima e dopo.

## 7. VPN e collaudo

- Scegliere il ruolo WireGuard e la topologia; evitare sottoreti sovrapposte e definire accessi di gestione.
- Configurare chiavi fuori da Git, firewall, routing, DNS e MTU per il caso scelto.
- Misurare prima Ethernet senza VPN, poi tunnel: throughput, latenza, CPU, RAM ed eventuali perdite.
- Provare reboot, ripristino del tunnel, DNS e IPv6; se il ruolo è client VPN, definire e provare il comportamento quando il tunnel cade.
- Eseguire una prova continuativa iniziale di almeno 24 ore e registrare anomalie e limiti.

**Uscita:** funzione VPN verificata con obiettivi prestazionali concordati sui risultati reali, senza assumere numeri dagli appunti.

## 8. Manutenzione

Conservare patch piccole e motivate, configurazione minima, riferimenti ai commit e registro delle prove. Ricompilare dopo gli aggiornamenti della base; i moduli kernel devono corrispondere esattamente al kernel della build. Non puntare i feed a una release diversa per simulare un upgrade della distribuzione.

Prima di dichiarare il progetto mantenibile, provare anche un aggiornamento tra due build e il recupero da una configurazione non funzionante. Valutare l'invio delle patch a monte dopo la stabilizzazione: l'accettazione non è garantita.

## Prossima sessione

Obiettivo circoscritto: studiare offline il bootloader e il layout dal backup, chiarire l'errore della lettura raw/OOB e identificare una base R3 ricompilabile. Predisporre inoltre una seconda copia su supporto indipendente. Il primo flash dipende dalla procedura concreta di recupero e dalla validazione dell'immagine; nessuna immagine è ancora selezionata.
