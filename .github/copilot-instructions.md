# U1FA development instructions for GitHub Copilot

This repository is the private development repository for U1 Filament Automation (U1FA).

## Safety first

- Never send commands to a real Snapmaker U1 from tests, examples, CI, or generated code.
- Never modify live Snapmaker Orca profiles in tests. Use temporary directories, fixtures, mocks, or the U1FA sandbox.
- Never create, edit, or delete real Spoolman vendors, filaments, or spools in tests. Mock the service or use explicit test data.
- Never install, replace, or patch printer firmware, Klipper configuration, Adaptive PA files, macros, or calibrators automatically.
- Printer setup/install operations must preserve the existing U1FA safety model: read/plan first, compatibility checks, backups, explicit user confirmations, and fail-closed behavior for unknown files.
- Do not weaken checks that block writes while the printer is busy or while a calibration is active.
- Do not bypass SHA-256 verification or the verified-package requirement in the updater.

## Repository and release architecture

- Development work belongs in this private repository.
- The public repository `ubaccu/u1-filament-automation` remains the release/update endpoint until the release architecture is explicitly changed.
- Do not publish a release, tag, installer, source archive, or development branch to the public repository unless explicitly requested.
- Do not change `DEFAULT_GITHUB_REPOSITORY` away from the approved public release repository without an explicit migration plan and updater compatibility test.

## Code quality

- Prefer small, reviewable changes with dedicated tests.
- Run the complete unittest suite before merging.
- Preserve Italian and English UI behavior when changing user-facing text.
- Keep dashboard rendering read-only: rendering a page must not contact the printer or write to Spoolman, Orca, or Adaptive PA state.
- Use mocks and temporary paths for external services and filesystem integration tests.
- Keep changes reversible and avoid unrelated refactors in safety-sensitive patches.

## Licensing and attribution

- Preserve `LICENSE`, `THIRD_PARTY_NOTICES.md`, required copyright notices, and attribution for third-party GPL components.
- Do not remove or weaken third-party license obligations while refactoring or packaging.
