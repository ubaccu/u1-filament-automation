# Language / Lingua

**English** | [Italiano](INSTALLAZIONE_STAMPANTE.md)

# Installing U1FA AutoPA Mod on the Snapmaker U1

This procedure installs **U1FA AutoPA Mod** on a Stock U1 and manages its three
components as one protected setup.

U1FA manages three components:

- the active Klipper module
  `/home/lava/klipper/klippy/extras/flow_calibrator.py`;
- `/home/lava/printer_data/config/adaptive_pa_macro.cfg`;
- the corresponding include in `printer.cfg`, when required.

## Connection addresses

U1FA does not contain a preset printer IP address. On first launch, the
**Connections** page asks for:

- the IP address or hostname shown by the Snapmaker U1;
- an optional Spoolman address. Leave it blank to use automatic discovery.

Discovery checks Spoolman on the current computer (`127.0.0.1` always means the
user's own computer), endpoints advertised by Moonraker/PAXX, and the U1 on the
standard Spoolman port `7912`. A manual address can be supplied for another host
or non-standard port.

**Verify and save** performs read-only Moonraker and Spoolman requests and derives
the SSH target as `root@HOST`. Only the two service addresses are stored in the
current operating-system account. The SSH password is never saved.

## Requirements

- the print has finished and the U1 is completely idle;
- Moonraker is reachable;
- SSH Root Access is enabled, using either a key or password;
- the original or modified calibrator has a recognized SHA-256.

Before printer setup, enable both touchscreen options:

1. **Settings → Maintenance → Advanced Mode → Agree → Enable** — enables Fluidd;
2. **Settings → Maintenance → Root Access → Agree → Open** — enables SSH for
   backup and protected installation.

If the user has not changed it, the default SSH password for this configuration
is `snapmaker`. U1FA shows this only as a reminder and never stores it.

macOS already includes an SSH client. Windows needs **OpenSSH Client** from
Optional Features; OpenSSH Server is not required. On Linux install
`openssh-client` if `ssh` is unavailable. U1FA checks for the client and does not
install system components itself.

## Guided desktop procedure

1. Open U1FA while the printer is completely idle.
2. Configure and verify the U1 and Spoolman addresses.
3. Select **Check printer setup**.
4. Confirm that Advanced Mode and Root Access have been enabled.
5. Enter the SSH password only when requested.
6. Run the read-only check first.
7. Stop immediately if U1FA reports `unknown`, `unknown-blocked`, an unexpected
   SHA-256 or a printer that is not idle.
8. Review the exact files and operations shown in the preview.
9. Only if every component is recognized, complete both confirmations to apply
   the modification.

Before every write U1FA checks printer state and file hashes again. Existing
files receive exclusive timestamped backups. Writes are atomic and verified;
failure triggers rollback.

The application does not send `RESTART` or `FIRMWARE_RESTART`. After an actual
installation or restore, completely power off the U1, wait 10–15 seconds and
power it on again. A soft Klipper restart does not reload the modified Python
module reliably on this machine.

## Read-only CLI check

The desktop workflow is recommended for normal users. The equivalent technical
check is:

```bash
u1fa printer-check \
  --ssh-target root@U1_IP \
  --moonraker-url http://U1_IP \
  --ask-ssh-password
```

It reads Moonraker printer state and the SHA-256 values of the calibrator and
Adaptive PA macro. It also verifies that `APA_COIL_RUN_ULTRA` is loaded by
Klipper. No G-code or file write is performed.

## CLI preview and application

Preview without writing:

```bash
u1fa printer-install \
  --ssh-target root@U1_IP \
  --moonraker-url http://U1_IP
```

Protected application:

```bash
u1fa printer-install \
  --ssh-target root@U1_IP \
  --moonraker-url http://U1_IP \
  --apply \
  --confirm-printer-write
```

The protected order is:

1. verify Moonraker and Snapmaker machine state;
2. read and compare SHA-256 values;
3. verify print state a second time;
4. block unknown calibrators and macros;
5. recognize exact and glob includes in `printer.cfg`;
6. create exclusive timestamped backups;
7. validate the modified Python file;
8. perform atomic writes with matching ownership and permissions;
9. verify final SHA-256 values and roll back on failure;
10. request a full power cycle only when files were actually written.

## Restore

Use the guided desktop restore whenever possible. The technical command is:

```bash
u1fa printer-restore \
  --ssh-target root@U1_IP \
  --moonraker-url http://U1_IP \
  --backup-path /home/lava/klipper/klippy/extras/BACKUP_NAME \
  --apply \
  --confirm-printer-write
```

The backup must match a validated original SHA-256 and must either have been
created by U1FA with the `flow_calibrator.py.U1FA_BACKUP_` prefix or be the
recognized historical original backup. A full power cycle is required after an
actual restore.

## Firmware updates

A Snapmaker firmware update may restore or change the original calibrator. Do
not copy an older file over it manually. Run **Check printer setup** again and
allow only the read-only check until the new original is recognized. See
[Firmware compatibility](FIRMWARE_COMPATIBILITY.md).

## Development sandbox

The local sandbox is for development and does not connect to the printer:

```bash
u1fa printer-install --sandbox-root ~/Downloads/u1fa-printer-sandbox --apply
```

It mirrors the U1 file layout locally and tests the calibrator, macro and include
without SSH or HTTP access to the real printer.
