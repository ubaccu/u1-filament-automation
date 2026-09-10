# U1FA AutoPA Mod Setup and Recovery

[Italiano](INSTALLAZIONE_STAMPANTE.md) | **English**

This guide describes the protected setup of **U1FA AutoPA Mod** on the Snapmaker U1. U1FA manages these components together:

- the active module `/home/lava/klipper/klippy/extras/flow_calibrator.py`;
- the macro `/home/lava/printer_data/config/adaptive_pa_macro.cfg`;
- the corresponding include in `printer.cfg`, only when required.

## Before you start

The printer must be completely idle. Do not run setup or recovery during a print or while a calibration is active.

Enable these options on the U1 touchscreen:

1. **Settings → Maintenance → Advanced Mode → Agree → Enable** — makes Fluidd/Moonraker available;
2. **Settings → Maintenance → Root Access → Agree → Open** — enables SSH for backup and protected installation.

If the user has not changed it, the default SSH password is `snapmaker`. U1FA may show it as a reminder, but **does not store it**.

## U1 and Spoolman discovery

For first setup, use **Check printer setup**.

U1FA can search the local network for a Snapmaker U1 only when the user explicitly starts discovery. Discovery:

- uses read-only Moonraker HTTP requests;
- identifies Moonraker through `/server/info`;
- confirms the expected U1 printer objects before accepting a result;
- sends no G-code, starts no movement, performs no heating and modifies no files;
- asks for confirmation before saving the discovered endpoint.

Manual IP/hostname configuration remains available if automatic discovery does not find the printer.

After the U1 is verified, U1FA can discover Spoolman from the expected local/Moonraker/PAXX sources and the standard U1 Spoolman port. A manual address can still be supplied for another host or a non-standard port.

## Computer requirements

- **macOS:** an SSH client is already included;
- **Windows:** **OpenSSH Client** is required only for protected printer-file configuration; OpenSSH Server is not required;
- **Linux:** install `openssh-client` if the `ssh` command is unavailable.

U1FA detects a missing client and does not install system components automatically.

## Recommended desktop workflow

1. Open U1FA while the printer is completely idle.
2. Verify or discover U1/Moonraker and Spoolman.
3. Open **Check printer setup**.
4. Confirm that Advanced Mode and Root Access are enabled.
5. Enter the SSH password only when requested.
6. Run the **read-only check** first.
7. Stop if U1FA reports `unknown`, `unknown-blocked`, an unexpected SHA-256 or a printer state that is not idle.
8. Review the exact files and actions shown in the preview.
9. Apply changes only when every component is recognized and after the explicit confirmations requested by the application.

Before every write, U1FA checks printer state and file hashes again. Existing files receive exclusive timestamped backups; writes are atomic and verified. If an error occurs, the protected flow uses its rollback path.

U1FA **does not send** `RESTART` or `FIRMWARE_RESTART` to complete setup. After a real installation or restore, fully power off the U1, wait 10–15 seconds and power it on again.

## Read-only technical check

For advanced users, the CLI equivalent is:

```bash
u1fa printer-check \
  --ssh-target root@U1_IP \
  --moonraker-url http://U1_IP \
  --ask-ssh-password
```

The check reads Moonraker/Snapmaker state and the SHA-256 values of the required components. It sends no G-code and writes no files.

## Technical preview

```bash
u1fa printer-install \
  --ssh-target root@U1_IP \
  --moonraker-url http://U1_IP
```

Without `--apply`, the command shows planned operations without writing to the printer.

## Protected technical application

```bash
u1fa printer-install \
  --ssh-target root@U1_IP \
  --moonraker-url http://U1_IP \
  --apply \
  --confirm-printer-write
```

Safeguards include:

1. verify Moonraker and Snapmaker machine state;
2. read and compare SHA-256 values;
3. verify printer state a second time immediately before writing;
4. block unknown calibrators or macros;
5. recognize expected includes in `printer.cfg`;
6. create exclusive timestamped backups of files being changed;
7. syntax-check the modified Python file;
8. perform atomic writes with matching permissions and ownership;
9. verify final state and roll back on failure;
10. request a full power cycle only after an actual write.

## Technical restore

```bash
u1fa printer-restore \
  --ssh-target root@U1_IP \
  --moonraker-url http://U1_IP \
  --backup-path /home/lava/klipper/klippy/extras/BACKUP_NAME \
  --apply \
  --confirm-printer-write
```

The backup must match a validated original and satisfy U1FA's accepted backup criteria. After an actual restore, fully power off the printer, wait 10–15 seconds and power it on again.

## Firmware updates

After every Snapmaker firmware update, do not manually copy the old calibrator over the new one. Run **Check printer setup** again and stop at the read-only check if the original file is not recognized.

See [U1 firmware compatibility](FIRMWARE_COMPATIBILITY.md).

## Development sandbox

During development and testing, use the local sandbox instead of the real printer:

```bash
u1fa printer-install --sandbox-root ~/Downloads/u1fa-printer-sandbox --apply
```

The sandbox mirrors the required file layout in a local folder and opens no SSH or HTTP connection to the U1.
