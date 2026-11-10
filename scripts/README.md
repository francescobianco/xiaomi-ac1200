# Strumenti del laboratorio R3

Questi script descrivono le operazioni della sessione del 10 novembre 2026 sul nostro **R3, firmware 2.26.39**. Non sono un installer generico. Gli indirizzi attuali sono router `192.168.31.1` e dongle `192.168.31.222`, interfaccia `wlxe0b2f1c5819b`.

Dipendenze locali usate: Python 3, `requests`, `cryptography`, NetworkManager/`nmcli`. Erano già disponibili sul PC. Non sono stati installati pacchetti sul router.

| File | Effetto |
| --- | --- |
| `probe_router.py` | Legge informazioni pubbliche e verifica tre porte di gestione |
| `stock_session.py` | Gestisce login stock e conserva il token in `private/` |
| `setup_stock.py` | Prepara credenziali/profilo, configura il router e riconnette il dongle; fasi distinte |
| `probe_access.py` | Esegue uno script temporaneo tramite API amministrativa, usando `c_upload`/`netspeed`; riceve dati sull'interfaccia Xiaomi |
| `read_backup_tools.sh` | Legge geometria NAND e opzioni degli strumenti stock |
| `backup_nand.sh` | Acquisisce la NAND in lettura, a blocchi da 4 MiB, trasferendola al PC |
| `verify_backups.py` | Verifica dimensioni, digest remoti e locali e seconda lettura delle aree critiche |

Le fasi `prepare` e `configure` sono già state eseguite e **non vanno ripetute per riconnettersi**. Per riprendere il collegamento usare soltanto `setup_stock.py reconnect`, quindi `verify`. I file in `private/` sono necessari per questi comandi e contengono credenziali: non pubblicarli.

`probe_access.py --script ...` esegue lo script specificato come root: revisionarlo prima dell'uso. Il valore 1629 della risposta di upload non prova né il fallimento né il successo dell'esecuzione; servono evidenze di ritorno. Il programma attende il rapporto finale e scrive dettagli privati. Il backup rifiuta di sovrascrivere file già acquisiti: un tentativo interrotto richiede una revisione prima di ripartire.

Il trasferimento attuale non prevede autenticazione applicativa o TLS: è limitato all'interfaccia e all'IP del router, sulla rete Wi-Fi di laboratorio protetta. Il server resta in ascolto solo durante l'acquisizione. Non usarlo su reti condivise.

## Provenienza della via di accesso

- [xmir-patcher](https://github.com/openwrt-xiaomi/xmir-patcher), commit `16a46e350e3de2cb3415ab2cb652df53783998dc`, file `connect1.py`.
- [OpenWRTInvasion](https://github.com/acecilia/OpenWRTInvasion), commit `fcec03a49d78d700d62f7be82093bd8e349d9a55`, script principale e formato XML.

La prova locale adatta questa tecnica evitando i binari e le modifiche NVRAM/password/avvio degli strumenti originali. Non installa SSH, non modifica il bootloader e non scrive immagini firmware.
