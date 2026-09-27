# U1 Filament Automation 1.8.4

## Italiano

U1FA 1.8.4 è un hotfix mirato per il primo setup su PAXX 12-21.

- Corretto l'identificatore esatto della build PAXX supportata in `1.5.2-paxx12-21-2a88932`.
- Gli SHA-256 dei componenti Klipper PAXX già convalidati restano invariati.
- `adaptive_pa_macro.cfg` può essere assente prima del primo setup: U1FA la crea automaticamente durante l'installazione protetta.
- Il controllo firmware non presenta più la macro non ancora installata come componente firmware mancante.
- Migliorata la diagnostica del `BUILD_VERSION` PAXX.
- Nessuna modifica alla logica Adaptive PA, agli asset AutoPA, ai profili Orca o al supporto Snapmaker U1 2.0.0.205 rispetto alla 1.8.3.

## English

U1FA 1.8.4 is a focused hotfix for first-time setup on PAXX 12-21.

- Corrects the exact supported PAXX build identifier to `1.5.2-paxx12-21-2a88932`.
- Previously validated PAXX Klipper component SHA-256 values remain unchanged.
- `adaptive_pa_macro.cfg` may be absent before first setup: U1FA creates it automatically during the guarded installation flow.
- The firmware preflight no longer presents a not-yet-installed macro as a missing firmware component.
- Improves diagnostics for a mismatched PAXX `BUILD_VERSION`.
- No changes to Adaptive PA logic, AutoPA assets, Orca profiles, or Snapmaker U1 2.0.0.205 support compared with 1.8.3.
