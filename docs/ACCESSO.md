# Verifica preliminare dell'accesso R3

Data: 10 novembre 2026. Le sezioni preliminari descrivono lo stato prima della configurazione; vedere l'esito effettivo qui sotto e il registro.

## Esito della sessione software

Configurazione stock completata, Wi-Fi protetto e nuova password amministrativa verificati. La via `c_upload`/`netspeed`, adattata senza modifiche NVRAM e senza installazione SSH, ha eseguito codice con UID 0 e restituito l'inventario al PC. I sorgenti e le istruzioni sono in [scripts](../scripts/README.md).

Acquisiti 32 blocchi ECC da 4 MiB, con MD5 remoto/locali coincidenti e SHA-256 locali. Seconda lettura identica per Bootloader, Config, Bdata e Factory. Dump combinato locale: `backups/2026-11-10/full-ecc.bin`.

La modalità raw con OOB ha fallito durante il primo blocco con errore I/O; non è disponibile una copia raw completa. L'acquisizione con ECC e la seconda lettura sono invece riuscite. [Esito della verifica](evidence/2026-11-10-backup-verification.json).

Non è stato provato un ripristino, né creata una seconda copia su supporto indipendente. Il backup dell'overlay è stato acquisito online e non è una fotografia atomica del filesystem. Questi limiti vanno risolti o valutati esplicitamente prima dell'installazione.


## Evidenza diretta

Il [rapporto della sonda](evidence/2026-11-10-probe.json) registra la risposta dell'API pubblica `xqsystem/init_info`: hardware R3, firmware 2.26.39, lingua cinese, `inited=0`. Le connessioni TCP alle porte 22, 23 e 122 sono state rifiutate. Questo non dimostra l'assenza di servizi su ogni altra porta.

La rete del PC presenta una route per 192.168.31.0/24 sul dongle e una sola route predefinita IPv4 via Ethernet. Il profilo `xiaomi-setup` era già attivo con autoconnect disabilitato: non è stato necessario modificarlo.

Il percorso `/cgi-bin/luci/` restituisce 404, mentre `/cgi-bin/luci/web` porta alla guida iniziale. Il codice della pagina `/cgi-bin/luci/web/init/hello` contiene il flusso di autenticazione iniziale del produttore. Non è stato invocato né sono state impostate password.

## Strumento esaminato

Repository: [openwrt-xiaomi/xmir-patcher](https://github.com/openwrt-xiaomi/xmir-patcher).

Commit scaricato: `16a46e350e3de2cb3415ab2cb652df53783998dc`.

Copia di analisi temporanea: `/tmp/xiaomi-xmir-audit`; non è un archivio permanente del progetto. Nessun suo script è stato eseguito o importato.

Letture effettuate: `connect.py`, `connect1.py`, parti di `gateway.py`, `create_backup.py`, `data/payload_ssh/exp10it.sh` e configurazione/avvio Dropbear.

- La tabella modelli include R3. Il dispatcher indirizza i modelli precedenti a R2100 verso `connect1.py`; questo è un indizio di supporto previsto, non una prova sul firmware 2.26.39.
- Il rilevamento richiede configurazione iniziale completata (`inited=1`).
- Il payload previsto abilita parametri UART/boot tramite NVRAM con commit, imposta una password root predefinita e avvia SSH. Può installare file e collegamenti di avvio persistenti.
- Il payload usa un eseguibile Dropbear incluso nel repository: l'audit del wrapper non verifica provenienza e comportamento del binario.
- La configurazione inclusa consente autenticazione root con password. Prima dell'impiego occorre definire credenziali robuste e limitare l'accesso alla rete di laboratorio.
- Il backup incluso usa `dd` sulle partizioni MTD in blocchi temporanei. Non va descritto come acquisizione raw NAND con OOB né come ripristino già garantito.

Non eseguire il menu completo alla cieca: comprende anche installazione di firmware e bootloader, che sono attività diverse dall'accesso amministrativo.

## Passo successivo preparato

1. Completare l'identificazione dall'etichetta e chiarire la disponibilità di UART/recupero.
2. Preparare la configurazione iniziale, con credenziali conservate in `private/`, e verificare come riconnettere il dongle dopo il cambio Wi-Fi.
3. Scegliere una via di accesso con modifiche minime; valutare se adattare la procedura per evitare password predefinite e modifiche non necessarie all'ambiente di avvio.
4. Solo dopo ottenere inventario e backup; nessuna immagine è ancora selezionata per il flash.

Per ripetere la sola lettura informativa dal PC:

```bash
python3 scripts/probe_router.py --output docs/evidence/nuova-sessione.json
```

Il comando non configura il router, non tenta autenticazioni e non avvia lo sblocco. Non sovrascrivere evidenze precedenti quando si registrano nuove sessioni.
