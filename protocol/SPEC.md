# DeskPort control extensions: v1 baseline

Recorded 2026-09-17 from the existing desktop and Apple implementations. This is
the shared contract for binding roles and display control, not a redesign of the
wire protocol. Clipboard payloads and GameStream media remain out of this document's
scope. Existing product documents provide operational context, not alternate wire
definitions. Any future normative behavior change must add compatibility tests.

## Transport and trust

The default binding/control rendezvous is TCP 48991, distinct from the streaming
port family; callers must retain configured binding ports. Control uses TLS 1.2+
and newline-delimited UTF-8 JSON objects. Display and Apple binding receive buffers
are bounded to 32768 bytes. Do not apply this limit to desktop clipboard payloads.
TLS credentials and platform-specific trust/storage remain in consumer adapters.

Known peers pin certificates. Initial binding uses explicit approval/TOFU, not a
public-CA assertion of a person's identity. Display control requires a previously
approved client certificate with persisted ready/granted access and an available
exclusive display controller. A JSON capability is not authorization.

## Binding and feature metadata

The host sends `hello` with `meta.version: 1`. Existing metadata includes
`clientBinding: 1`, `endpointRefresh: 1`, `clipboard: 1` and `adaptiveDisplay: 0|1`.
These are independently interpreted feature advertisements. This extraction adds
neither a version nor a capability bitset.

Client-only binding sends `request` with a UUID `tx` and metadata containing
`version: 1`, `clientBinding: 1`, `role: "client"`, and a nonempty name (at most
64 characters, without control characters). It must not claim host identity,
streaming certificate or host port. The approved path is:

`hello -> request -> pending -> accept -> ready -> client-ready -> bound`.

The host sends `accept`/`ready`; the client sends `client-ready` only after the
matching transaction is approved and ready. The client does not provision a local
host. Desktop mutual binding instead exchanges host metadata and grants on both
sides. Neither flow implies a distributed atomic commit or automatic revocation
at the other device. Binding persistence/TLS failure tests stay in each product.

## Display lease

After an authenticated `hello` advertises `adaptiveDisplay: 1`, a client sends:

```json
{"type":"display-resize","seq":1,"width":1920,"height":1080,"scale":2}
```

Width/height are backing pixels, aligned to four, within 640..7680 and 360..4320;
scale is 1 or 2. The client policy additionally aims for a 960x540 logical desktop
but that recommendation is not the wire minimum. Server validation is authoritative.
The pure core proposal may be invalid for extreme aspect ratios; validate before
requesting it. Logical points must be converted to pixels exactly once.

Clients increment positive request sequence numbers and allow one resize in flight.
The current server accepts a positive sequence when no resize is pending; it does
NOT enforce strictly increasing sequences between completed requests. Do not claim
replay rejection that this implementation does not provide. It correlates helper
completion to the pending request.

Success: `display-result` echoes `seq`, `width`, `height` (additional fields are
allowed). Failure: `display-result` with `seq` and `error`. Clients validate the
sequence and dimensions and fall back to fixed-size behavior after failure.

The optional request field `textCaret: true` subscribes that lease to `text-caret`
updates. Missing/false means no updates. It is a subscription, not evidence of
host support. Desktop clients currently omit it; Apple requests it. Keep this
legacy field until a separately tested negotiation migration is needed.

After acquiring the lease, clients send `display-ping`; the host sends
`display-pong`. A ping before a lease is rejected. Control ownership is scoped to
the authenticated connection; disconnect/revocation releases it. Lease/watchdog,
video-stop barriers and idle restore timers remain consumer lifecycle policy.
Desktop and Apple currently send heartbeats at five seconds but have different
response deadlines; this extraction deliberately does not unify their timers.

Caret messages contain `caret.valid` and normalized `caret.x/y` in [0,1]. Apple
accepts finite numeric coordinates and reports invalid samples as invalid rather
than moving the viewport. OS coordinate acquisition and keyboard avoidance remain
platform adapters. The legacy desktop client does not subscribe to these messages.

## Compatibility and tests

Unknown object fields are tolerated by the scoped display handlers. Unknown message
types are not automatically tolerated: the Apple display handler fails its channel,
and an active host display channel rejects unexpected messages. Send unsolicited
messages only to peers that opted in. Do not tighten existing parsing in a mechanical
extraction (Qt and Foundation have different numeric conversion behavior).

`display-cases.json` covers legacy requests without caret subscription, optional
subscription, unknown fields, invalid dimensions/scale/sequence, result correlation
and caret validation. Desktop tests send requests through the production TLS server;
Apple tests feed results/carets through the production handler and retain loopback
TLS tests. These are compatibility baselines, not full old-binary interoperability
or real-device streaming acceptance. Future capability migrations need explicit
old-host/new-client and new-host/old-client integration cases.
