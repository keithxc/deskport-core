# DeskPort Core

Small, platform-independent contracts and workspace policy shared by
[DeskPort](https://github.com/keithxc/deskport) clients. Legacy modules are
GPL-3.0-or-later; the standalone `portable/` module is MIT. See LICENSE,
portable/LICENSE and NOTICE.md.

[DeskPort Desktop 2.9.0](https://github.com/keithxc/deskport/releases/tag/v2.9.0)
uses the portable workspace and stream arithmetic and reply validators in its
desktop adapter. The release notes link to the exact core commit in the
provenance record. For package selection and supported device pairing, see the
[DeskPort installation guide](https://github.com/keithxc/deskport#install).

`i18n/` owns the English-keyed UI translation table, platform usage, locale
registry and offline manual text. Native UI adapters generate their resources
from this table; wire identifiers never pass through localization. See
[the localization contract](i18n/README.md).

The legacy workspace and protocol headers use header-only C11, also consumable
by C++ and Objective-C. The portable module includes
[header-only policy and typed contracts](portable/API.md) and generated C and
Java catalog definitions.

- `include/deskport/workspace.h`: drawable-pixel workspace proposal and validation.
- `include/deskport/protocol.h`: existing control-message names.
- `protocol/SPEC.md`: scoped v1 contract and known implementation differences.
- `fixtures/workspace.json`: explicit results for core and platform adapters.
- `protocol/display-cases.json`: old/new display requests and error cases.
- `manual/manual.json`: the user manual bundled in every package; see `manual/README.md`.

No TLS, UI, Moonlight, persistent settings, input ownership or media pipeline lives
here. Window geometry, safe areas, keyboard avoidance and gestures remain native.

Run `python3 tests/test_workspace.py`, or configure CMake and run CTest. The test
runner accepts `--apple-header PATH` or `--qt-header PATH` to compile and exercise
the actual consumer adapter against the same fixtures (Qt requires qmake).

Consumers pin commits rather than following a branch. A core fix is implemented
and tested here first, then each consumer updates its pin and runs its adapter,
transport and platform tests. Library revision and on-wire version are independent.
New protocol functionality needs old/new peer cases before either consumer opts in.

## Public rules for independent consumers

The new [portable catalog](portable/README.md) is separately MIT-licensed and
contains generated C/Java definitions for ports, tuning and display policy. The
existing workspace implementation and protocol headers remain GPL-3.0-or-later.
Consumers planning proprietary distribution must use only appropriately licensed
components; the catalog does not change the licenses of their other dependencies.

## Test output paths

The direct Python test entry points select checked temporary and compiler-cache
paths through the shared mygit resolver when it is installed. On mm4 the
verified external build volume is required. Elsewhere the existing host and CI
temporary storage remains usable, including with older shared resolvers. Raw
CMake, compiler and GUI invocations bypass this guard and require explicit output
paths and disk verification. Generated tracked source remains in its maintained
source location.
