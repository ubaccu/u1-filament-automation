# U1FA 1.8.3b4 — standard Orca Slicer profile mirroring

## Italiano

Build di sviluppo successiva alla 1.8.3b3. La grafica esistente resta invariata.

- eredita firmware 1.5.2, PAXX v21, firmware 2.0.0.205 e coda sequenziale 2–4 bobine;
- gli asset firmware 2.0.0.205 incorporati sono ora byte-per-byte identici ai file realmente validati sulla U1, eliminando la precedente doppia impronta dovuta alla copia del sorgente;
- aggiunge il backend sicuro per portare i profili U1FA da Snapmaker Orca a Orca Slicer standard;
- vengono accettati soltanto profili U1FA completamente materializzati e senza dipendenza `inherits` dalla base Snapmaker;
- un profilo Orca Slicer già esistente e non gestito da U1FA non viene mai sovrascritto;
- un profilo identico può essere adottato in sicurezza e da quel momento viene seguito tramite SHA-256;
- se un profilo mirror viene modificato manualmente fuori da U1FA, gli aggiornamenti successivi vengono bloccati;
- gli aggiornamenti gestiti creano un backup prima della sostituzione atomica;
- la GUI mostra l'opzione soltanto quando Orca Slicer standard viene rilevato in modo univoco;
- l'attivazione richiede conferma esplicita e Snapmaker Orca resta lo slicer principale;
- dopo l'attivazione, nuovi profili e risultati PA vengono riportati anche nel mirror standard; un conflitto blocca il mirror senza sovrascrivere.
- pacchetti verificati su Windows x64, Linux x86_64, macOS Intel e macOS Apple Silicon;
- archivio sorgente GPL corrispondente verificato separatamente;
- gli asset firmware 2.0.0.205 incorporati sono controllati tramite SHA-256 e corrispondono byte-per-byte ai file validati sulla U1 reale.

## English

Development build following 1.8.3b3. The existing visual layout remains unchanged.

- inherits firmware 1.5.2, PAXX v21, firmware 2.0.0.205 and the sequential 2–4 spool queue;
- bundled firmware 2.0.0.205 assets are now byte-for-byte identical to the files validated on the real U1, removing the previous dual fingerprint caused by source copying;
- adds a safe backend for mirroring U1FA profiles from Snapmaker Orca to standard Orca Slicer;
- only fully materialized U1FA profiles with no live Snapmaker `inherits` dependency are accepted;
- an existing standard Orca profile not managed by U1FA is never overwritten;
- an identical existing profile may be safely adopted and then tracked by SHA-256;
- if a mirrored profile is manually changed outside U1FA, later updates are blocked;
- managed updates create a backup before atomic replacement;
- the GUI shows the option only when standard Orca Slicer is detected unambiguously;
- enabling requires explicit confirmation and Snapmaker Orca remains the primary slicer;
- after opt-in, new profiles and PA results are mirrored to standard Orca; a conflict blocks the mirror without overwriting.
- packages validated on Windows x64, Linux x86_64, macOS Intel and macOS Apple Silicon;
- matching GPL source archive validated separately;
- bundled firmware 2.0.0.205 assets are SHA-256 checked and byte-for-byte identical to the files validated on the real U1.
