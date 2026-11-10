# Analisi del recupero prima dell'installazione

## Risultati osservati

Il backup logico combinato supera la verifica SHA-256 locale. I due kernel stock hanno header uImage e payload con CRC validi. [Analisi offline](evidence/2026-11-10-offline-analysis.json).

| Elemento | Risultato |
| --- | --- |
| Bootloader | Stringa U-Boot 1.1.3, 12 aprile 2016 |
| Kernel0 | Offset 0x200000, slot da 4 MiB, payload 2256483 byte |
| Kernel1 | Offset 0x600000, slot da 4 MiB, payload 2247546 byte |
| Avvio corrente | `flag_boot_rootfs=0`, `flag_last_success=0`, `flag_boot_success=1` |
| Tentativi falliti | `flag_try_sys1_failed=0`, `flag_try_sys2_failed=0` |
| Console stock | `boot_wait=off`, `uart_en=0`, `bootdelay=5` |
| Kexec stock | `sys_kexec_load` coincide con `sys_ni_syscall`: chiamata non implementata |

Questi parametri sono stati soltanto letti. `bootcmd=tftp` è un valore osservato nell'ambiente, ma il router si avvia normalmente dalla NAND: non si deve dedurne che basti predisporre un server TFTP per pilotarlo.

Il bootloader contiene messaggi di menu per caricare un sistema in RAM via TFTP e per scrivere la flash. Non abbiamo dimostrato come selezionare questi percorsi senza console. Nessun riavvio di prova o cambio di flag è stato eseguito.

## Layout della candidata X-Wrt

Le prime partizioni coincidono per offset e dimensioni con lo stock. Il profilo standard però usa:

| Area | Offset | Dimensione | Effetto rispetto allo stock |
| --- | --- | --- | --- |
| kernel_stock | 0x200000 | 4 MiB | Corrisponde al kernel0 |
| kernel | 0x600000 | 4 MiB | Corrisponde al kernel1 |
| ubi | 0xa00000 | 118 MiB | Unifica rootfs0, rootfs1 e overlay |

**Preservare kernel0 da solo non preserva un sistema stock avviabile:** se il nuovo sistema usa o riformatta rootfs0, il kernel originale perde il suo filesystem. Anche i futuri sysupgrade possono coinvolgere lo spazio UBI unificato.

L'etichetta `read-only` del Device Tree è utile nel sistema nuovo ma non prova la correttezza del programma che esegue il primo flash sullo stock.

## Vie da valutare

1. **Profilo standard X-Wrt:** richiede un piano di ripristino completo, oltre ai backup. Le ricette comunitarie scrivono kernel1 e rootfs0 e modificano l'ambiente. Non sono state eseguite.
2. **Variante sperimentale che preservi lo stock attivo:** studiare un Device Tree con UBI confinata alla sola rootfs1 e kernel nuovo in kernel1, conservando kernel0, rootfs0 e overlay. È un'ipotesi progettuale, non una procedura approvata: prima occorre verificare la selezione dei kernel nel bootloader, i flag di successo e gli script di upgrade. Non è stata applicata alcuna patch di questo tipo.
3. **Recovery stock tramite USB/TFTP:** verificare la procedura esatta per R3 e per questo bootloader, procurare un'immagine originale adatta e distinguere il caricamento in RAM dalla scrittura in flash. I riferimenti a R3G non sono sufficienti.

Una seconda copia del backup su supporto indipendente resta da creare. Una copia aggiuntiva sullo stesso SSD non soddisfa questo requisito. Il dump raw/OOB è incompleto e il comportamento del driver vendor va chiarito; non presentare il dump logico come immagine raw pronta da riscrivere con un programmatore.

## Aggiornamento

L'analisi del 10 novembre sera ha trovato la recovery USB nell'initramfs dei kernel stock. Piano completo in [INSTALLAZIONE.md](INSTALLAZIONE.md).

## Condizioni prima del flash

La scheda di installazione deve indicare immagine e hash, dimensioni controllate, layout effettivo, partizioni coinvolte, modifiche ai flag e recupero previsto. Se resta necessario accettare il rischio di un recupero tramite seriale, va descritto concretamente insieme all'immagine pronta: l'autorizzazione a proseguire senza seriale non rende un fallback non provato affidabile.
