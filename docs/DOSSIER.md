# Dossier del progetto

Data: 10 novembre 2026. Proprietario del dispositivo: Francesco.

## Obiettivo

Riutilizzare un router Xiaomi inutilizzato come nodo Linux domestico, con WireGuard e piccoli servizi compatibili con le sue risorse. Conservare nel repository configurazioni, patch e istruzioni sufficienti a ricompilare e aggiornare il firmware.

Due risultati distinti: far avviare un sistema alternativo e mantenerlo aggiornato. Il primo non garantisce il secondo. Anche il firmware originale è già basato su Linux: il progetto riguarda ottenere controllo amministrativo e un sistema sostituibile e mantenibile.

## Provenienza delle informazioni

La conversazione incollata è una testimonianza della sessione precedente, non un log tecnico completo: molti output sono abbreviati e l'ultimo comando risulta interrotto. Qui «riportato» significa osservato dall'assistente precedente secondo quegli appunti; non significa riconfermato sul dispositivo in questa sessione.

| Elemento | Dato di lavoro | Stato dell'evidenza |
| --- | --- | --- |
| Modello | Xiaomi Mi Router 3, R3 | Riconfermato via API; etichetta fisica da confrontare |
| Firmware | MiWiFi 2.26.39, cinese | Verificato via API e uname |
| Indirizzo gestione | 192.168.31.1 | Verificato sul collegamento Wi-Fi di laboratorio |
| SoC atteso | MediaTek MT7620A | Coerente con il supporto comunitario R3; da leggere sul dispositivo |
| RAM | MemTotal 124772 KiB, coerente con 128 MB fisici | Verificato via esecuzione root il 10 novembre |
| Flash | NAND 128 MiB, pagina 2048 byte, OOB 64, eraseblock 128 KiB | Verificato via sysfs e log; ID produttore 0x92, chip 0xf1; modello commerciale da identificare |
| Ethernet attesa | Fast Ethernet, 100 Mbit/s | Da confermare con link e hardware; non Gigabit |
| USB | Porta USB presente secondo gli appunti | Da verificare fisicamente e nel sistema |
| Wi-Fi | Due bande; rete aperta dopo reset | Riportato; funzionamento dei driver alternativi da provare |
| Accesso root | Esecuzione tramite API stock dimostrata | Callback uid=0 e inventario; SSH non installato |
| Backup | NAND completa con ECC verificata; raw/OOB fallito | 128 MiB più seconda lettura iniziale; dump esclusi da Git; ripristino non provato |
| Flash alternativo | Non documentato | Nessuna installazione riuscita dimostrata |

Non usare immagini per R3G, R3P/3 Pro, R3C, R4A o RB02: sono dispositivi differenti. L'identità R3 resta il presupposto da verificare prima di ogni lavoro specifico sulla flash.

## Sintesi della sessione precedente

1. Il dispositivo era stato descritto genericamente come Xiaomi AC1200; le prime ipotesi 4A/RB02 sono state superate dall'identificazione R3.
2. Il PC risultava collegato via Ethernet al FRITZ!Box. È stato inserito un dongle Realtek RTL8188EU, interfaccia riportata `wlxe0b2f1c5819b`.
3. L'accensione della radio Wi-Fi aveva attivato un profilo FRITZ!Box salvato; l'assistente riferisce di averlo scollegato.
4. La rete Xiaomi inizialmente era protetta. Francesco ha effettuato un reset fisico; in seguito è stata rilevata la rete aperta `Xiaomi_632D_9CD2`.
5. L'assistente riferisce di essersi collegato con un profilo temporaneo, lasciando Internet sul cavo, e di aver letto modello R3 e firmware 2.26.39.
6. L'ultimo tentativo di ispezione è stato interrotto dal sistema dell'altro assistente. Non si può dedurre che tutti i suoi comandi siano stati annullati: eventuali file scaricati o modifiche parziali vanno controllati.

Il router era descritto come ancora da configurare. Lo stato attuale della procedura guidata, del profilo Wi-Fi e del collegamento WAN non è noto.

## Supporto software: verifica delle fonti

Le fonti sono state consultate il 10 novembre 2026. I link ai rami mobili descrivono il contenuto consultato, non una revisione già fissata per una build.

### OpenWrt e derivati

- Il [progetto storico XFY9326](https://github.com/XFY9326/Xiaomi-R3-OpenWrt-Stable/blob/main/README.md) dichiara una base 21.02.0 ed è archiviato. È una traccia tecnica, non una base di produzione già approvata.
- La [patch comunitaria per 22.03](https://gist.github.com/devbis/fbb09215640273a6e257914f1f7c6887), pubblicata nel gist nel 2024, aggiunge supporto alla scheda e modifiche NAND/upgrade per kernel 5.10. Smentisce l'idea che esista esclusivamente lavoro su 21.02; non certifica stabilità o manutenzione attuale.
- Il [profilo MT7620 di OpenWrt main](https://raw.githubusercontent.com/openwrt/openwrt/main/target/linux/ramips/image/mt7620.mk) consultato non contiene `xiaomi_miwifi-r3`. Questo controllo non equivale a un censimento di tutte le release e di tutti i fork.
- **Correzione dopo il clone Git:** X-Wrt alla revisione `61de4809b444b7a3d3c0a9cc27c1e0d6702572e4` contiene il profilo R3, il Device Tree e il driver NAND per kernel 6.18.60. Il precedente riscontro via pagina web era incompleto. Vedere [base di build e sorgenti fissati](BUILD.md).
- La [wiki MIR3](https://openwrt.org/toh/xiaomi/mir3) resta un riferimento da confrontare con i sorgenti e con il dispositivo; le istruzioni storiche non vanno trascritte direttamente in comandi di flash.

È stata scelta X-Wrt come base moderna candidata e avviata la compilazione locale. Non è ancora selezionata alcuna immagine per il flash né verificato l'avvio su hardware. Prima di scrivere un port NAND nuovo, proviamo il supporto già presente.

### Accesso amministrativo

[xmir-patcher](https://github.com/openwrt-xiaomi/xmir-patcher) è uno dei progetti da esaminare. La via di accesso di riferimento è stata successivamente adattata e provata sul nostro R3 2.26.39: esecuzione root dimostrata senza installare il payload completo di xmir-patcher. Non assumere che una procedura per un altro Xiaomi funzioni qui.

Configurazione iniziale, sblocco e abilitazione SSH possono modificare file o impostazioni persistenti. La precedente formula «passi senza rischi» era troppo assoluta: vanno registrati comportamento e modifiche di ogni strumento.

## Vincoli del porting

La NAND è un punto centrale, ma non l'unico. Vanno verificati controller, ECC/OOB, bad block, layout MTD/UBI, formato delle immagini, limiti del bootloader, Device Tree, Ethernet, Wi-Fi, ambiente di avvio e percorso di aggiornamento. Una compilazione riuscita dimostra soltanto che il codice compila.

La patch 22.03 tocca anche l'aggiornamento NAND: il progetto deve verificare sia il primo avvio sia gli upgrade successivi. Non trasferire offset o nomi di partizioni dalle guide senza confrontarli con l'unità reale.

Le prestazioni WireGuard non sono state misurate. Le stime della conversazione non costituiscono un requisito o un risultato. CPU, porte Ethernet, MTU e configurazione effettiva determineranno la velocità utile.

## Impiego previsto

Prima fase: laboratorio dietro il FRITZ!Box, gestione locale e un client di prova. Successivamente scegliere se WireGuard dovrà consentire accesso remoto alla casa, uscita tramite un provider VPN o collegamento tra reti. Il caso d'uso determina routing, firewall, DNS e prove di accettazione.

Un firmware storico può essere utile come riferimento sperimentale. Per l'uso continuativo occorrono una base mantenuta, aggiornamenti riproducibili e test reali. La posizione dietro il FRITZ!Box limita alcuni accessi ma non elimina le vulnerabilità.
