# Security Policy

[Italiano](#italiano) · [English](#english)

## Italiano

### Versioni supportate

È supportata l'ultima release U1FA pubblicata nella pagina GitHub Releases. Prima di segnalare un problema, verifica di utilizzare la versione più recente disponibile.

### Bug normali vs vulnerabilità

Per crash, problemi di interfaccia, profili non rilevati, errori di sincronizzazione o altri bug che **non** espongono dati e **non** permettono azioni non autorizzate, usa i normali moduli di [GitHub Issues](https://github.com/ubaccu/u1-filament-automation/issues/new/choose).

Per una possibile vulnerabilità di sicurezza, **non pubblicare dettagli tecnici sensibili in una Issue**. Usa **Security → Report a vulnerability** quando disponibile. Se la segnalazione privata GitHub non è disponibile, apri una Issue senza dettagli tecnici e chiedi un canale di contatto privato.

Non pubblicare password SSH, token, chiavi private, indirizzi IP non necessari, log completi, dati personali o altre informazioni riservate.

### Informazioni utili

Indica, quando rilevante:

- versione U1FA;
- sistema operativo;
- versione firmware U1;
- versione Snapmaker Orca;
- comportamento osservato e impatto potenziale;
- passaggi minimi per riprodurre il problema in sicurezza.

Invia log o file soltanto dopo avere rimosso credenziali e dati identificativi.

Sono particolarmente rilevanti: esecuzione di comandi non autorizzati, esposizione di credenziali, scritture sulla stampante senza conferma, aggiramento dei controlli di inattività o SHA-256, modifica di profili diversi da quello selezionato e aggiornamenti non verificati.

### Test responsabili

Esegui prove soltanto su dispositivi tuoi o per i quali disponi di autorizzazione. Non testare durante una stampa e non tentare di accedere a stampanti o account di altre persone.

---

## English

### Supported versions

The latest U1FA release published on GitHub Releases is supported. Before reporting a problem, verify that you are using the newest available version.

### Normal bugs vs vulnerabilities

For crashes, UI problems, profile-discovery errors, sync failures or other bugs that **do not** expose data and **do not** enable unauthorized actions, use the normal [GitHub Issues](https://github.com/ubaccu/u1-filament-automation/issues/new/choose) forms.

For a potential security vulnerability, **do not publish sensitive technical details in a public Issue**. Use **Security → Report a vulnerability** when available. If GitHub private vulnerability reporting is unavailable, open an Issue without technical details and request a private contact channel.

Do not publish SSH passwords, tokens, private keys, unnecessary IP addresses, complete logs, personal data or other confidential information.

### Useful information

When relevant, include:

- U1FA version;
- operating system;
- U1 firmware version;
- Snapmaker Orca version;
- observed behavior and potential impact;
- the minimum safe steps needed to reproduce the problem.

Send logs or files only after removing credentials and identifying information.

High-priority reports include unauthorized command execution, credential exposure, printer writes without confirmation, bypasses of idle-state or SHA-256 checks, modification of a profile other than the selected one, and unverified updates.

### Responsible testing

Test only devices you own or are authorized to use. Do not test during a print and do not attempt to access another person's printer or accounts.
