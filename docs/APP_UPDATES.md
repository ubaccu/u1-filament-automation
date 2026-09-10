# U1FA Application Updates

[Italiano](AGGIORNAMENTI_APP.md) | **English**

U1FA checks the project's public releases in the background at startup. This check concerns only the desktop application installed on the computer: **it does not inspect, update or restart Snapmaker U1 firmware**.

## How it works

1. The app reads public releases over HTTPS without using personal credentials.
2. A stable release considers only stable releases; a beta can receive later betas and stable releases.
3. U1FA selects only the package matching the current operating system and architecture: macOS DMG, Windows installer or Linux AppImage.
4. Before download, U1FA shows the release version, release notes, package size and SHA-256.
5. The download is first written to a temporary file and is accepted only when both size and SHA-256 match the published release data.
6. The user must separately confirm the download and the installer opening step.
7. U1FA never replaces its own executable while it is running.

## Public distribution channel

U1FA development is maintained separately from the public repository. The public repository contains end-user documentation, support and releases.

Every distributed release includes:

- packages for supported platforms;
- `SHA256SUMS.txt`;
- a version-matched GPL corresponding-source archive.

The built-in updater reads only this public channel and does not require a GitHub token or account.

## Snapmaker U1 firmware updates

Application updates and printer firmware updates are separate operations.

After a Snapmaker U1 firmware update:

1. open U1FA while the printer is completely idle;
2. use **Check printer setup**;
3. run the read-only check first;
4. if U1FA reports unknown firmware or unknown files, stop and do not force installation manually.

Read [U1 firmware compatibility](FIRMWARE_COMPATIBILITY.md) before applying printer-file changes.

## macOS

Current macOS packages are not Apple-notarized. After installing a new version, first launch may require **right-click / Control-click → Open → Open**. If macOS still blocks the application, use **System Settings → Privacy & Security → Open Anyway**.

Disabling Gatekeeper is not required and normal installation does not require `xattr` commands.
