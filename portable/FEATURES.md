# Consumer implementation matrix

Snapshot: 2026-09-20. `Integrated` means source wiring, not physical acceptance.
This matrix describes the migration boundary; product test records carry actual
run results. Keep entries explicit when introducing new capabilities.

| Feature | Desktop | Apple | Android | Source of truth |
| --- | --- | --- | --- | --- |
| Base-port family | Integrated C | Integrated C | Integrated generated Java | portable/catalog.json |
| Tuning choices/labels | Integrated C to Qt/QML | Integrated C to Foundation | Integrated generated Java | portable/catalog.json |
| Display-policy IDs | Legacy protocol adapter to catalog | Existing wire IDs, shared header | Generated validation | portable/catalog.json |
| Workspace sizing | Legacy GPL core | Legacy GPL core | Legacy GPL core via JNI | include/deskport/workspace.h |
| Session admission/takeover | Native adapter | Native adapter | Native adapter | protocol/SESSION_TAKEOVER.md |
| Session lifecycle/resume | Native desktop adapter | Not integrated | Not integrated | protocol/SESSION_LIFECYCLE.md |

Workflow: change a public contract/catalog; add reviewed compatibility cases;
generate and check output; wire each native adapter; run its fixture harness and
platform checks; update this matrix; commit core before consumer pins. Publish a
core revision before pushing a consumer that references it. Git and Nix pins must
agree. Products and host activation remain independently controlled.
