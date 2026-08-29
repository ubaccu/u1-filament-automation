# Third-Party Notices

## U1FA AutoPA Mod

- Sviluppo e integrazione della modifica: Ivan Riccelli / Bottega3DLab e
  contributori U1FA.
- Nome tecnico interno della catena: `CHAIN v6`.
- Licenza del progetto e delle modifiche derivate: GNU GPL v3.0.

U1FA AutoPA Mod integra e adatta il flusso di calibrazione automatica alla
Snapmaker U1. I crediti seguenti riguardano i componenti e il lavoro upstream da
cui deriva una parte del sistema, non la paternità del nome o dell'integrazione
U1FA AutoPA Mod.

## U1 Adaptive Pressure Advance Auto Calibration

- Autore/manutentore: djsplice e contributori
- Sorgente: https://github.com/djsplice/u1-adaptive-pa-autocal
- Licenza: GNU General Public License v3.0

Il modulo Adaptive PA conserva il backup v6 recuperato e ne legge offline i
risultati. Le modifiche derivate restano sotto GNU GPL v3.0 e mantengono questo
avviso e i crediti upstream.

Si riconoscono inoltre:

- Snapmaker U1 flow calibrator e misura del residuo induttivo `area`;
- OrcaSlicer Adaptive Pressure Advance;
- CNC Kitchen e PrusaPATuner come ispirazioni metodologiche indicate dall'upstream.

Klipper, firmware Snapmaker, Moonraker, OrcaSlicer e Spoolman rimangono soggetti alle
rispettive licenze. Progetto indipendente e non affiliato ai soggetti citati.

I file recuperati da firmware o progetti terzi sono inclusi esclusivamente per
tracciabilità, confronto e applicazione della patch; questo repository non cambia né
pretende di sostituire le rispettive licenze originarie.

## Strumenti e runtime della distribuzione desktop

I pacchetti desktop incorporano oppure usano in fase di build i seguenti progetti,
che restano soggetti alle proprie licenze:

- Python, Python Software Foundation License:
  https://docs.python.org/3/license.html
- PyInstaller, GNU GPL con eccezione specifica per la distribuzione dei bootloader:
  https://pyinstaller.org/en/stable/license.html
- AppImageKit/appimagetool e runtime AppImage, licenza MIT:
  https://github.com/AppImage/AppImageKit/blob/master/LICENSE
- Inno Setup, usato per generare l'installer Windows secondo la propria licenza:
  https://jrsoftware.org/files/is/license.txt

OpenSSH Client non viene incorporato né installato automaticamente. Su Windows e
Linux U1FA utilizza il client già presente nel sistema esclusivamente per la
configurazione protetta dei file sulla stampante.
