# DeskPort Core

Small, platform-independent contracts and workspace policy shared by DeskPort's
desktop and native clients. Legacy modules are GPL-3.0-or-later; the standalone
`portable/` catalog is MIT. See LICENSE, portable/LICENSE and NOTICE.md.

The initial implementation is header-only C11, also consumable by C++ and
Objective-C. Keeping this small arithmetic policy inline avoids adding a library
link step to pinned upstream projects. There is one implementation, not generated
copies. A compiled library can be introduced when there is enough code to need it.

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
