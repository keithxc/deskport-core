# Experimental Seamless / App Mode protocol

This document defines the version 1 control contract introduced for the
experimental Linux server to Linux Wayland client path. It does not change the
existing Desktop Mode contract. Version 1 first establishes explicit mode
negotiation and a bounded window lifecycle; no implementation may claim that
surface media, input, resize, or a headless compositor works merely because mode
negotiation succeeds.

## Isolation and transport

Desktop Mode remains the default. An absent `sessionMode`, or an explicit value
of `desktop`, means Desktop Mode. A host that supports this contract advertises
`hello.meta.seamlessMode: 1` on the existing pinned, mutually authenticated
control connection to an approved peer. The capability is not authorization and
does not replace binding, certificate checks, exclusive session admission,
revocation, or lease fencing.

Milestone 1 implements a one-shot capability preflight, not Seamless session
admission. On an approved peer connection, a client may ask whether both ends
agree on the mode and version:

```json
{"type":"seamless-negotiate","sessionMode":"seamless","seamlessVersion":1}
```

The host answers exactly once:

```json
{"type":"seamless-result","sessionMode":"seamless","seamlessVersion":1,"accepted":true}
```

or rejects it without changing modes:

```json
{"type":"seamless-result","sessionMode":"seamless","seamlessVersion":1,"accepted":false,"code":"unsupported-version"}
```

A client must not send `seamless-negotiate` unless the host advertised the
capability. Only version 1 is accepted. An explicit Seamless request is never
silently downgraded to Desktop Mode. The host sends one result and closes this
preflight control connection. `accepted: true` proves only capability, mode, and
version compatibility. It does not acquire or reserve a session, start a
compositor/sidecar, launch an application, create a window, or authorize media or
input. A real authenticated, exclusive Seamless session lease is a separate gate
that must be implemented before Milestone 3. Preflight success or failure does not
mutate an existing Desktop session.

Rejected results carry the stable machine-readable field `code`. They may also
carry a bounded human-readable `error`, but consumers must branch only on `code`.

All messages in this document use newline-delimited UTF-8 JSON on the existing
control connection and begin with `seamless-`. The serialized JSON object before
the newline is at most `DP_SEAMLESS_CONTROL_FRAME_LIMIT` (32768) bytes. Receivers
check that limit before JSON parsing and allocation. JSON numbers used as integer
fields must actually be integral, finite numbers in range; strings and booleans
are not numeric alternatives.

Encoded pixels never use this JSON channel, including as Base64. Frames and
damage records use a separately negotiated authenticated binary media plane bound
to the same pinned peer identity and a future admitted Seamless session lease.
The mode preflight alone does not negotiate a media byte layout. Milestone 1
therefore sends no media records; a later session/media capability must freeze
lease admission, framing, and codec negotiation before either peer sends them.

## Identifiers and bounds

The server assigns each top-level window an integer `id` from 1 through
2147483647. Zero, negative, fractional, string, and boolean IDs are invalid. An ID
is unique for the entire future admitted Seamless session and is not reused after
a window is destroyed. At most 64 windows may be active; the initial
implementation may intentionally enforce the narrower one-window MVP.

Window sizes are visible backing pixels:

| Property | Limit |
| --- | --- |
| Width | 16 through 7680 |
| Height | 16 through 4320 |
| Sequence | 1 through 2147483647 |
| UTF-8 title | at most 1024 bytes |
| UTF-8 app ID | at most 255 bytes |
| Encoded media payload | 1 through 33554432 bytes |

Unlike Desktop display sizes, surface sizes need not be aligned to four pixels.
An encoder may pad internally but must retain the visible width and height in its
metadata. A damage rectangle has positive width and height, nonnegative origin,
and must lie entirely inside the current visible window size. Validate encoded
payload length before allocating or decoding it.

## Control messages

The lifecycle names below reserve the version 1 schemas and isolation boundary.
They are not enabled by a successful Milestone 1 preflight. Until the exclusive
Seamless lease gate exists, sending any of them is `wrong-session-mode` and must
not start a sidecar or mutate window state.

Directions are server-to-client (`S->C`) and client-to-server (`C->S`). Every
message after negotiation carries the current `id`. Unknown or retired IDs fail;
they never create an implicit window.

| Type | Direction | Required version 1 fields and behavior |
| --- | --- | --- |
| `seamless-window-create` | S->C | `id`, `width`, `height`; optional bounded string `title` and `appId`. Creates exactly one new ID. |
| `seamless-window-destroy` | S->C | `id`; optional bounded `reason`. This is the authoritative end of the ID. |
| `seamless-window-title` | S->C | `id`, bounded string `title`. |
| `seamless-window-resize-request` | C->S | `id`, positive `seq`, valid `width`, `height`. Only one request per window may be pending. |
| `seamless-window-resize-result` | S->C | matching `id` and `seq`, then either the observed valid `width` and `height`, or a nonempty `error`. Success changes the current visible size. |
| `seamless-window-close` | C->S | `id`. Requests compositor/application close; it does not retire the ID. Retirement occurs only on `seamless-window-destroy`. |
| `seamless-window-focus` | C->S | `id`, boolean `focused`. Focus does not authorize input for another window. |
| `seamless-window-cursor` | S->C | `id` and cursor metadata. Cursor pixel framing is deferred with the media plane. |
| `seamless-input-pointer` | C->S | `id` and pointer state scoped to that window. Exact button/scroll schema is deferred until the input milestone. |
| `seamless-input-keyboard` | C->S | `id` and keyboard state scoped to that window. Exact keymap/modifier schema is deferred until the input milestone. |
| `seamless-protocol-error` | Either | stable nonempty `code`; optional human `error`, `id`, and `seq` only when those fields passed strict parsing. It does not acknowledge a state mutation. |

The cursor and input names are reserved by version 1 so Desktop messages cannot
be repurposed accidentally. A consumer must not send them until the corresponding
schema/capability is implemented and advertised. Unknown fields on an otherwise
valid known message may be ignored for forward compatibility. Missing, duplicate,
or wrongly typed required fields are errors.

Generic binding/session lifecycle messages continue to be handled by their
existing contracts. Desktop-only messages such as `display-resize` are never
interpreted as a Seamless window resize. Conversely, a Desktop session must not
dispatch any `seamless-*` message to a Desktop handler. A mode mismatch is a
protocol failure, not feature discovery.

## Binary media plane

The semantic media record kinds are:

- `DP_SEAMLESS_MEDIA_FRAME`: a complete encoded visible window frame.
- `DP_SEAMLESS_MEDIA_DAMAGE`: an encoded update associated with an in-bounds
  damage rectangle.

Both carry the negotiated version, window ID, positive per-window sequence,
visible size, encoded payload length, and codec/framing metadata defined by the
future media capability. A record for an unknown/destroyed ID, wrong version,
invalid size or rectangle, or payload above
`DP_SEAMLESS_ENCODED_FRAME_LIMIT` is rejected before decode. A static window sends
no media record; liveness belongs to the control plane rather than dummy frames.

This separation is normative: newline JSON controls window/session state, while
encoded data is binary and independently flow-controlled. Backpressure or a bad
media record must not cause a parser to reinterpret bytes as control JSON.

## Failure and state rules

Implementations use stable error strings from `protocol.h`. At minimum:

- `mode-not-advertised` for negotiation sent without the advertised capability;
- `unsupported-version` for any version other than 1;
- `wrong-session-mode` for Seamless traffic on a Desktop session;
- `control-too-large` before parsing an oversized JSON control frame;
- `duplicate-window-id` for an active or previously retired ID;
- `unknown-window-id` for lifecycle, input, or media referencing no active ID;
- `invalid-window-size` for invalid visible size or damage bounds;
- `frame-too-large` for a zero-length or oversized encoded payload;
- `media-not-negotiated` when media arrives before its separate capability is
  successfully negotiated.

Validation failure performs no partial state mutation. An implementation may
send one bounded `seamless-protocol-error`, then closes the affected Seamless
channel according to its existing authenticated-session policy. Revocation,
takeover, transport loss, or session release destroys all active window IDs and
media state; resume policy must never duplicate them.

## Compatibility vectors

[`seamless-cases.json`](seamless-cases.json) covers the legal lifecycle, wrong
version, duplicate and unknown IDs, invalid dimensions, oversized control/media
frames, pre-negotiation media, and Desktop/Seamless isolation. The accompanying
Python test compiles the production header as C11 and C++17 and executes the
stateful vectors. These are protocol checks, not compositor, rendering, input,
VPS, or physical streaming acceptance.
