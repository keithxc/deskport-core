# MIT portable consumer API

This directory is independently usable with its MIT license. These additions are
original public contracts and pure arithmetic; they do not operate a connection
or define a native controller. Include `deskport/workspace.h`,
`deskport/session.h`, `deskport/stream_budget.h` or `deskport/input.h` as needed.
Functions are header-only C11, also usable from Objective-C and C++11. Math
functions may require linking the platform math runtime (`-lm`).

The complete new declarations are in the named headers; the generated Java
class provides constants and `long` field predicates only.

## Workspace values

```c
typedef struct { int width, height, scale; } DPWorkspace;
int dp_workspace_valid(DPWorkspace value);
int dp_workspace_equal(DPWorkspace a, DPWorkspace b);
DPWorkspace dp_workspace_from_encoded(int width, int height, int scale);
DPWorkspace dp_workspace_from_viewport(double width, double height, double density);
DPWorkspace dp_workspace_tuned(DPWorkspace base, double tuning);
DPWorkspace dp_workspace_for_viewport(double width, double height,
                                    double density, double tuning);
```

Encoded width/height are four-pixel-aligned backing dimensions in the existing
640..7680 by 360..4320 protocol box. Scale is 1 or 2. Invalid constructors return
`{0,0,0}`; field equality can be true for invalid values, so validate separately.
The encoded constructor validates without multiplying or resizing. The viewport
constructor calls the existing `dp_view_workspace` exactly once. Tuning calls
`dp_tuned_desktop_size`, which owns the supported factors, invalid-factor fallback,
aspect ratio, quantization and orientation-aware host minimum. The combined
constructor calls viewport then tuning; it introduces no second sizing policy.

Encoded 824x1416, scale 2, at tuning 1.0 **or** 1.2 becomes 1200x2064, scale 2.
Logical 824x1416 at density 2 instead produces 1648x2832 before tuning.
Encoded 1920x1200, scale 1, at tuning 1.2 becomes 1600x1000. Transient geometry,
NaN/infinity and invalid densities defer sizing; invalid tuning alone uses 1.0.

## Drawable compatibility, explicit adjustment and advertised modes

These additive entry points are in `deskport/workspace.h`:

```c
DPWorkspace dp_workspace_from_drawable_pixels(double width, double height, double density);
DPWorkspace dp_workspace_from_drawable_viewport(double width, double height, double density);
DPWorkspace dp_workspace_adjust(DPWorkspace base, double tuning);
DPWorkspace dp_workspace_for_host(DPWorkspace base);
DPWorkspace dp_workspace_for_macos(DPWorkspace base);
DPWorkspace dp_workspace_for_windows(DPWorkspace base);
DPWorkspace dp_workspace_for_saver(DPWorkspace base);
DPWorkspace dp_workspace_select_mode(DPWorkspace request, const DPWorkspace *modes, int count);
```

Choose the conversion by the rectangle's meaning. The existing
`dp_workspace_from_viewport` retains its logical UI contract and protocol minimum
640x360. The **drawable** constructors implement the separate public desktop
golden contract. From pixels, density in [0.5,8] maps to backing scale 1 for
<=1, otherwise 2; requested dimensions multiply by `scale / min(density,2)`.
From a logical drawable viewport, multiply by `max(scale,density)` exactly once.
Fit the preferred backing size to the fixed-axis 1920x1080 desktop floor, then
the 7680x4320 ceiling, preserving aspect until four-pixel upward quantization.
The public portrait golden requires a width floor too (1488x2200 becomes
1920x2840); this floor is not an orientation-swapped long-edge-only rule.

Nonfinite/nonpositive pixels or density outside [0.5,8] return `{0,0,0}`.
The pixel proposal deliberately preserves the public core/Qt extreme-aspect
result `{4,4320,1}` for `(1,100000,1)`: it is **not wire-valid**. Always validate
before sending. A native value adapter can map the zero proposal to its own
failure sentinel; it must not reimplement sizing. The logical drawable viewport
requires both logical edges >=128 and validates the final proposal, returning
zero for transient/unrepresentable rectangles. Encoded input still goes through
`dp_workspace_from_encoded` without density conversion.

`dp_workspace_adjust` divides by a supported catalog tuning factor, fits only
the protocol box and rounds each dimension upward to four pixels; scale is
unchanged. Factor matching uses the existing MIT tuning tolerance (strictly
within 0.000001). Unsupported factors, including NaN/infinity, preserve a valid
base. An invalid base returns zero. For example 1920x1080 scale 2 /1.5 gives
1280x720 scale 2, and 2316x1152 /1.3 gives 1784x888.

`dp_workspace_for_host` applies the existing orientation-aware 800x600 logical
floor (portrait 600x800) at the base scale, still within the wire box; impossible
floors return zero. The macOS/Windows names are identical aliases. For two-step
semantics, call `for_host(adjust(base,tuning))`: quantize the protocol adjustment
first, then use that result's aspect for the host floor. This is deliberately
distinct from the unchanged `dp_workspace_tuned`, which preserves the original
aspect and quantizes only once. For 824x1416 scale 2 at 1.2, the two-step result
is 1200x2060; existing tuned remains 1200x2064. Saver divides encoded dimensions
by their scale, applies the protocol minimum, quantizes and returns scale 1.
It does not apply a host floor; compose explicitly when required.

Mode selection validates the request, signed count 0..96, and **every** list
entry before ranking. An empty list preserves the valid request (pointer may
be null); a nonempty null list, any invalid mode/scale, or illegal count returns
`{0,0,0}`. The caller supplies readable storage for `count` values throughout the
call. The wire documentation does not prescribe a ranking. This new MIT API
uses an original lexicographic rule, in this order:

1. Same portrait classification (`height > width`; square is nonportrait).
2. Smaller absolute aspect error `abs(mode.width/mode.height - request.width/request.height)`, compared as exact bounded rational values.
3. Smaller squared backing-pixel distance `(mode.width-request.width)^2 + (mode.height-request.height)^2`.
4. Earlier advertised entry on a complete tie.

Scale is validated but does not rank dimensions. Return the selected mode's
own scale, without rotation or synthesis. Thus request 1300x748 scale 2 with
ordered modes 1920x1080, 1280x720, 1080x1920 (all scale 1) selects 1280x720 scale 1;
a 1080x1920 scale 2 request selects the portrait mode at scale 1.

```c
#include "deskport/workspace.h"
/* logical drawable rectangle; use from_viewport for logical UI geometry */
DPWorkspace base = dp_workspace_from_drawable_viewport(400, 225, 2);
DPWorkspace adjusted = dp_workspace_adjust(base, 1.5); /* 1280x720, scale 2 */
DPWorkspace host = dp_workspace_for_host(adjusted);    /* 2136x1200, scale 2 */
DPWorkspace modes[] = {{1920,1080,1}, {1280,720,1}, {1080,1920,1}};
DPWorkspace selected = dp_workspace_select_mode(adjusted, modes, 3);
/* Check dp_workspace_valid(host/selected) before proposing a display change. */
```

The ratio/proposal helpers in the header are implementation details, not separate
adapter policies. `portable/test_workspace_compat.py --work <directory> --json
<file>` compiles a copy of only MIT headers in C11/C++11 and Objective-C on macOS,
with address/undefined/float-cast-overflow sanitizers. Its standalone fixtures
record only public input/output facts; no legacy implementation is included.
These APIs do not establish a completed native integration or migration.

## Desktop compatibility arithmetic

Use `desktop_workspace.h` for the existing desktop path from drawable pixels
through optional saver scaling, tuning and the host floor. It preserves the
`960 × 540` initial minimum per unit of backing scale, the original binary
floating-point rounding at each stage and the relative-size/aspect score for
advertised modes. The mode list represents scale-one physical modes. Pass
already validated wire data when adapting a peer's mode advertisement.

`desktop_stream.h` provides the desktop automatic and saver ceilings. Automatic
bitrate truncates to whole kbps before applying the 4:4:4 multiplier. Saver uses
the reference rate at 8 fps, with bounds of 500–4000 kbps. Preference defaults,
saved manual limits, cadence changes, and the reconnect decision belong to the
desktop adapter. The logical viewport and stream-budget entry points above and
below remain available to independent consumers.

## Data vocabulary and parsed-field validation

`catalog.json` generates `contracts.h` and `DPContracts.java`. Existing display
policy IDs, validation and defaults stay in `catalog.h` / `DPCatalog`. The new
files expose message names (`DP_MESSAGE_*`), capability names/versions
(`DP_CAP_*`), protocol sizes, sequence/rate bounds, and documented deadline
values. A deadline constant never schedules a timer. Only version 1 is currently
supported; unknown versions do not imply compatibility.

`dp_contract_*` predicates accept wide signed integers so overflow-sized decoded
numbers can be rejected before narrowing. Java uses equivalent `long` predicates
such as `sequenceValid`, `workspaceValid` and `virtualKeyValid`. A typed predicate
does not validate JSON types: parsers must separately reject boolean-as-number,
fractional, missing and wrongly typed fields before calling. Keep authentication,
certificate validation, capability negotiation and ownership in the adapter.
Their names are `boolean_valid`, `version_supported`, `sequence_valid`,
`rate_valid`, `workspace_valid`, `hid_key_valid`, `virtual_key_valid`,
`modifiers_valid`, `button_valid`, and `input_kind_valid` after that prefix.

`session.h` adds the following pure predicates:

| Function | Meaning |
| --- | --- |
| `dp_session_reply_valid(busy, admitted)` | Strict booleans; busy and admitted cannot both be true. |
| `dp_session_reply_state(busy, admitted)` | Invalid -1, rejected 0, occupied 1, admitted 2; local result identifiers only. |
| `dp_session_takeover_allowed(confirmed, same_connection, current_challenge)` | All three verified facts must be exactly 1. Reconnect never supplies confirmation. |
| `dp_resume_resize_allowed(same_authenticated_peer, token_matches, reservation_matches, resumed)` | All four verified facts must be exactly 1, including successful reservation resume. |
| `dp_display_result_valid(pending_seq, result_seq, requested, width, height, has_error)` | Exact pending request, valid requested workspace and echoed dimensions, no error. |
| `dp_pause_result_valid(pending_seq, result_seq, requested, observed, has_error)` | Exact sequence and strict paused boolean echo, no error. |
| `dp_rate_result(pending_seq, result_seq, requested_kbps, observed_kbps, live, has_error)` | Invalid/error -> `DP_RATE_ACK_TERMINATE`; valid live -> `DP_RATE_ACK_APPLIED`; valid non-live -> `DP_RATE_ACK_RESTART`. |
| `dp_event_in_scope(admitted, opted_in, active_generation, event_generation)` | Both flags true and equal nonzero adapter-owned lease/controller generations. |
| `dp_caret_valid(in_scope, valid, x, y)` | In-scope valid caret, finite coordinates in [0,1]. |

Flags use `int`; sequences use `int64_t`; workspace uses `DPWorkspace`; generation
IDs use `uint64_t`; caret coordinates use `double`. All functions return `int`.
Each channel has its own pending sequence. Pass zero pending sequence for an
unsolicited/missing acknowledgment, then terminate on failure. The adapter owns
the timeout, one-request-in-flight rule, saver echo validation when present,
matching-token checks within grace, input release, media stop and controlled
restart. Generation IDs are local freshness facts, never trusted claims in an
incoming message. Display correlation adds no new monotonic sequence rule.

## Bitrate and daily budget

```c
int dp_bitrate_automatic(int width, int height, double fps, int full_chroma);
int dp_bitrate_saver(int automatic_kbps);
int dp_bitrate_normal(int automatic_kbps, int manual_kbps);
int dp_bitrate_effective(int automatic_kbps, int manual_kbps, int saver);
int dp_bitrate_start(int automatic_kbps, int manual_kbps, int saver,
                     int admitted_live_rate);
uint64_t dp_bytes_nonnegative(int64_t value);
uint64_t dp_bytes_add(uint64_t total, uint64_t increment);
uint64_t dp_bytes_delta(uint64_t previous, uint64_t current, int has_previous);
uint64_t dp_budget_threshold(uint64_t limit, unsigned percent);
int dp_budget_level(uint64_t used, uint64_t limit);
```

Automatic bitrate is 15000 kbps times pixel ratio to 2560x1440, times
min(fps, `DP_BITRATE_MAX_FPS` = 120)/60,
doubled for full chroma (4:4:4), truncated to integral kbps and clamped to
5000..80000. Geometry must be positive and fps finite and positive; this rate
estimator does not validate the workspace protocol box. Invalid input returns
zero. For example, 2560x1440 at 120 or 240 fps gives 30000 kbps without full
chroma (60000 with full chroma). NaN/infinite fps is rejected before the cap.
Full chroma and saver flags are strict booleans. A zero result is a reject/defer
sentinel: the adapter must validate the chosen start rate before starting media.
The calculation retains binary floating-point evaluation and truncation, rather
than exact decimal arithmetic; values near an integer can truncate one kbps lower.

Saver is automatic/4, truncated, clamped to 3000..12000. A positive manual cap
is retained within wire bounds 500..200000; zero/negative manual selects the
automatic value. Effective saver is the minimum of normal and saver caps. An
invalid automatic estimate prevents calculation of a saver cap, even if manual
is valid. `dp_bitrate_start` requires the adapter to supply an **admitted and
negotiated** live-rate lease flag; true starts at the normal ceiling so saver can
later turn off. Legacy starts at effective cap. These functions never change
stored user preferences or mutate a normal ceiling.

Signed negative byte samples normalize to zero. Byte totals saturate at
`UINT64_MAX`. A first cumulative sample (`has_previous = 0`) contributes its
current value, ignoring `previous`: `(0, 123, 0)` gives 123. A reset counter also
contributes its current value: `(200, 30, 1)` gives 30. Otherwise the delta is
current minus previous. Invalid `has_previous` (neither 0 nor 1) gives zero.
Calendar boundaries, local-midnight resets, sampling and persistence belong to
the adapter. Budget zero disables warning levels. Positive budgets return normal
(0), warning (1) at 70%, critical (2) at 85%, exceeded (3) at 100%. Thresholds use
integer ceilings, including for budgets smaller than 100 bytes, without overflow.
`dp_budget_threshold` supports 0..100 percent; larger percentages return
`UINT64_MAX` as an invalid sentinel. Budget classification never stops media.

## Compact input vocabulary

`DP_HID_KEY_*` identifies keyboard-page physical usages. `DP_MOD_*` retains
left/right positions in HID modifier-byte order. `dp_input_modifier_for_hid(int)`
returns that modifier bit or zero. ISO non-US backslash (0x64), International1..5
(including JIS locations), navigation, punctuation, keypad and modifier keys
retain their official values. `DP_VK_*` and the validator cover a selected WinVK
subset plus digit, letter, keypad and F1..F24 ranges. Rejection means unsupported
by this compact contract, including all unassigned/reserved bytes; it is not a
complete classification of the Windows namespace. No layout-dependent HID-to-VK
conversion table is supplied.

`DP_LOCAL_BUTTON_*` (primary, secondary, middle, back, forward) and `DP_LOCAL_INPUT_*`
(key down/up, pointer absolute/relative, button down/up, scroll) are **local**
consumer identifiers. They are not new wire packet codes. Native adapters own
serialization, text input, keyboard layouts, event routing and focus/lifecycle.
All core predicates use the canonical `DP_LOCAL_*` values independently of wire
identifiers. Their existing numeric assignments are unchanged.

For source compatibility, C also exposes `DP_BUTTON_*` and `DP_INPUT_*` as aliases
by default. A native consumer with a separate wire vocabulary must define
`DP_DISABLE_LOCAL_INPUT_ALIASES` before its **first** portable header include,
preferably in its common entry header or compiler definitions:

```c
#define DP_DISABLE_LOCAL_INPUT_ALIASES
#include "deskport/input.h"
/* Use DP_LOCAL_BUTTON_MIDDLE for a local button; serialize explicitly. */
```

The guard is presence-based (even a definition of `0` disables aliases), applies
only to those legacy button/event aliases, and must be consistent across a
translation unit. It never disables `DP_HID_*`, `DP_VK_*` or `DP_MOD_*`.
Do not undefine aliases after inclusion: predicates must never depend on consumer
wire values. `generate.py` owns both the canonical constants and aliases.
Java's class namespace already separates these identifiers: `DPContracts` offers
both `LOCAL_BUTTON_*` / `LOCAL_INPUT_*` and the existing members with equal values;
its predicates use the canonical members.

`fixtures/local_namespace.c` is an independently authored synthetic consumer with
different wire enum values, opt-out and every portable header. `test_expansion.py`
compiles and runs it as C11/C++11 (also Objective-C on macOS), checks wire values,
local predicates and independent HID/WinVK, and tests default aliases separately.

## Product content and review

`content/apple-keys.json` provides the exact 26 added keys and maps 16 requirements
to existing canonical keys. Its `permissionKeys` names two original OS permission
explanations: local network discovery/connection to authorized computers, and
supported Bluetooth pointing devices. Each has original values in all 22 locales;
no legacy translation catalog was consulted. It also selects the corrected tuning explanation.
All 22 locales are complete with placeholder parity. New non-English translations
are machine-authored and await native-speaker review. Existing UI/guide values
remain intact; other notices and historical resources retain their own audit.
