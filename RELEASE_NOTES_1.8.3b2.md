# U1FA 1.8.3b2 — firmware 2.0 AutoPA validation build

## Italiano

Build di sviluppo per Snapmaker U1 firmware 1.5.2 e 2.0.0.205.

- mantiene il riconoscimento protetto del firmware tramite versione completa e SHA-256;
- usa asset AutoPA separati dalla linea firmware 1.5.2;
- integra la CHAIN Adaptive PA a cinque punti con LOOP=6;
- delega al firmware 2.0 la scelta algoritmo: LINEAR_FITTING su hotend standard e OS_DECEL su high-flow;
- usa APA_MEASURE_ONLY per restituire i cinque K senza sovrascrivere il Flow K nativo Snapmaker;
- ripristina il PA runtime precedente dopo ogni punto;
- conserva il cleanup stock e aggiunge 3 secondi di stabilizzazione termica prima di ogni campione K;
- mantiene bloccati firmware, dipendenze e file non riconosciuti;
- mantiene compatibilità separata con la linea Snapmaker 1.5.2;
- riconosce in modo protetto la build PAXX 1.5.2-paxx12-21-2a8893 solo quando gli hash convalidati corrispondono;
- corregge il packaging Windows degli asset LF protetti e migliora la diagnosi SSH su PAXX/Windows.

## English

Development build for Snapmaker U1 firmware 1.5.2 and 2.0.0.205.

- keeps exact version/SHA-256 guarded firmware recognition;
- separates firmware-2.0 AutoPA assets from the legacy 1.5.2 line;
- integrates the five-point Adaptive PA CHAIN with LOOP=6;
- delegates algorithm selection to firmware 2.0: LINEAR_FITTING on standard hotends and OS_DECEL on high-flow hotends;
- uses APA_MEASURE_ONLY so the five K measurements do not overwrite Snapmaker's native Flow K;
- restores the previous runtime PA after every point;
- preserves stock cleanup and adds 3 seconds of thermal stabilization before every K sample;
- unknown firmware, dependencies and files remain blocked;
- keeps the Snapmaker 1.5.2 firmware line supported separately;
- recognizes PAXX 1.5.2-paxx12-21-2a8893 only when the validated component hashes match;
- fixes LF-preserving Windows packaging for protected assets and improves SSH diagnostics on PAXX/Windows.
