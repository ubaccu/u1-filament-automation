# U1FA 1.8.3b1 — firmware compatibility test build

## Italiano

Questa build privata verifica la compatibilità con il firmware Snapmaker U1
2.0.0.205 e prepara il controllo per versioni future.

- riconosce il firmware e i componenti Klipper tramite versione completa e SHA-256;
- blocca installazione e calibrazione quando il firmware o un componente non è convalidato;
- tratta il vecchio AutoPA v6 su firmware 2.0.0 come incompatibile;
- include il calibratore stock 2.0.0.205 e un porting AutoPA dedicato, verificato
  tramite hash e test sandbox;
- consente l'installazione protetta solo sulla build esatta 2.0.0.205 con tutti
  gli hash convalidati, backup atomico e doppia conferma;
- abilita la calibrazione soltanto dopo aver riconosciuto anche il modulo AutoPA
  2.0.0 e la macro esatta;
- considera non sicuro uno stato macchina mancante o non interpretabile.

La versione è destinata esclusivamente al repository privato di sviluppo.

# English

This private build tests compatibility with Snapmaker U1 firmware 2.0.0.205
and lays out the fail-closed check for future versions.

- identifies firmware and Klipper components by full version and SHA-256;
- blocks installation and calibration when firmware or a component is not validated;
- treats legacy AutoPA v6 on firmware 2.0.0 as incompatible;
- bundles the stock 2.0.0.205 calibrator and a dedicated AutoPA port verified by
  hashes and sandbox tests;
- allows guarded installation only on the exact validated 2.0.0.205 build, with
  an atomic backup and two explicit confirmations;
- enables calibration only after both the 2.0.0 AutoPA module and exact macro
  have been recognized;
- treats a missing or unparseable machine state as unsafe.

This version is for the private development repository only.
