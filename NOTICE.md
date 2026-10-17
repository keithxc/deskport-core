# Source provenance

## Unified UI catalog — 2026-10-17

`i18n/` retains GPL-3.0-or-later for UI text imported from DeskPort's
Moonlight-derived Qt translation catalogs (desktop baseline d60e7bc8), the
authored DeskPort Client localization catalog (client baseline 5eac761) and the
existing shared manual (core baseline 4064059). Existing upstream Moonlight
translation contributors' rights are preserved. New translation drafts and
resource metadata are maintained separately from the MIT portable catalog.
No client implementation, vendored source, credentials or personal host data
is included in this import.

The workspace algorithm was extracted on 2026-09-17 from DeskPort
`app/backend/workspaceresolution.h` (desktop baseline 65fa57e0) and DeskPort Client
`Shared/DPViewport.h` (client baseline f84f796). The latter carries the
GPL-3.0-or-later identifier; this extraction retains that license. No upstream
Moonlight implementation, media SDK, credentials or platform assets are included.

The protocol documentation and fixtures describe DeskPort's existing extensions;
they do not replace upstream Moonlight/GameStream specifications.

## Independently authored portable catalog — 2026-09-20

`portable/` is a new MIT-licensed product-data and code-generation module. Its
license covers that directory only, including generated C/Java output. It does not
relicense `include/deskport/workspace.h`, `include/deskport/protocol.h`, their source
provenance, or any third-party code. The GPL headers may consume the MIT catalog;
the portable catalog never includes or imports those GPL headers.
