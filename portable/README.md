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

The portable view-size API accepts a logical rectangle and UI density. It fits a
backing workspace within the protocol bounds, aligns to four pixels, and returns
zero for transient or unrepresentable rectangles. The video-only fallback uses
even pixels and a 1920-pixel long edge.

## Product vocabulary and offline guide

The `content/` tables are covered by this directory's MIT license. They contain
original DeskPort interface copy and a guide written from product behavior.
The English interface text is the lookup key. The locale registry orders the
available languages, and the guide keeps its chapters and steps in reading order.
Translators can update one language while preserving placeholders, key names,
and the meaning of connection and permission prompts.

## Additive consumer contracts

See [API.md](API.md) for the MIT workspace value, session field validators,
stream bitrate/budget arithmetic and compact input vocabulary. Workspace wrappers
compose the existing view-size and tuning functions. Encoded dimensions carry
their scale as metadata; only a logical viewport is converted to backing pixels.
The native adapter retains TLS, parsing, ownership, timers, threads and lifecycle.

`catalog.json` also generates `include/deskport/contracts.h` and
`java/com/deskport/core/DPContracts.java`. Existing `DPCatalog` APIs and output
remain unchanged. Java supplies vocabulary and typed field predicates; native
workspace and stream arithmetic do not require a Java port.

Run `python3 portable/test_expansion.py --java` for standalone C11/C++11,
Objective-C (on macOS), Java and content fixtures. Use `--work <directory>` to
choose the temporary-output parent and `--json <file>` for a result record.
The test compiles against an isolated copy of the portable headers only.

`content/apple-keys.json` maps 42 product terms to 26 new and 16 existing keys, including two
original OS permission explanations in all 22 locales.
New consumers must use its `tuningGuidanceKey`: higher tuning values enlarge
remote controls; lower values provide more desktop space. The previous table
values are preserved for compatibility. New non-English values are machine
translations awaiting native-speaker review. [PROVENANCE.json](PROVENANCE.json)
records original authorship and official factual input sources.

Local event/button constants use `DP_LOCAL_BUTTON_*` / `DP_LOCAL_INPUT_*`.
Existing C aliases remain enabled unless `DP_DISABLE_LOCAL_INPUT_ALIASES` is
defined before the first portable include. HID/WinVK and modifier constants remain
available with aliases disabled. The expansion tests compile an actual synthetic
wire-enum consumer in C/C++ alongside the default compatibility consumer; see
[API.md](API.md) for the entry-header pattern and Java compatibility members.
