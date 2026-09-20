# Portable product catalog

Decision: 2026-09-20. The desktop and core remain public; a future independently
implemented mobile client may be proprietary. This newly authored MIT module
contains product constants and generated accessors, not Moonlight implementation
code. Its only dependency is the language runtime. Copying or building **only this
directory**, with its LICENSE, does not require any of the legacy GPL headers.
The rest of deskport-core retains its existing GPL license and provenance.

`catalog.json` owns the host port family, desktop tuning choices and display policy
IDs. `generate.py` emits `include/deskport/catalog.h` and
`java/com/deskport/core/DPCatalog.java`. These are generated artifacts, not two
hand-maintained policies. Run `python3 portable/generate.py` after a catalog edit;
CI/consumer tests must run `python3 portable/generate.py --check`.

Run `python3 portable/test_catalog.py --java` to check C11, C++11 and Java against
reviewed `cases.json`. The native tests use sanitizers. Consumers still own socket
reservation, DNS/IP parsing, persistence, localized labels and capability exchange.
An invalid base port yields control port zero, never a fallback endpoint.

Adding a feature requires a catalog/contract change, old/new-peer fixtures, each
native adapter, and its acceptance status. A new core pin alone does not implement
a feature. Do not add mobile UI, billing, credentials, platform SDKs or upstream
client code here. Do not infer that a current mobile binary is proprietary merely
because this directory is MIT; its existing dependencies remain separate blockers.
