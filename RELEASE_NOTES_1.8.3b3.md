# U1FA 1.8.3b3 — Orca discovery and sequential calibration foundation

## Italiano

Build di sviluppo successiva alla 1.8.3b2. La grafica esistente resta invariata.

- eredita il supporto separato per Snapmaker 1.5.2, PAXX 1.5.2-paxx12-21-2a8893 e firmware 2.0.0.205;
- rileva Snapmaker Orca e Orca Slicer standard come installazioni distinte, mantenendo Snapmaker Orca come preferenza attuale;
- non modifica automaticamente Orca Slicer standard in questa fase;
- introduce una coda sicura da 1 a 4 bobine con slot fisici e profili univoci;
- collega la coda al backend di calibrazione Adaptive PA in esecuzione strettamente sequenziale;
- ogni bobina viene completata e il relativo profilo viene aggiornato prima di passare alla successiva;
- al primo errore la coda si interrompe e non avvia le bobine restanti;
- il flusso singolo esistente resta disponibile e invariato;
- Fast Max Flow automatico resta fuori da questa build.

## English

Development build following 1.8.3b2. The existing visual layout remains unchanged.

- inherits separate support for Snapmaker 1.5.2, PAXX 1.5.2-paxx12-21-2a8893 and firmware 2.0.0.205;
- discovers Snapmaker Orca and standard Orca Slicer as separate installations while keeping Snapmaker Orca preferred;
- does not automatically modify standard Orca Slicer at this stage;
- introduces a safe 1-to-4 spool queue with unique physical slots and profile names;
- connects the queue to the Adaptive PA calibration backend using strictly sequential execution;
- each spool is completed and its profile updated before the next spool starts;
- the queue stops at the first error and does not start remaining spools;
- the existing single-calibration flow remains available and unchanged;
- automatic Fast Max Flow remains out of scope for this build.
