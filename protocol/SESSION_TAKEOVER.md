# Session admission and confirmed takeover (version 1)

2026-09-19: Prevent a new viewer from starting a second Sunshine stream after
losing the exclusive display lease. Base binding protocol version stays 1.

## Negotiation and lifecycle

A host advertises `hello.meta.sessionTakeover: 1`. A ready, granted peer must use
its pinned, mutually authenticated display TLS connection for admission **before**
resizing or launching/resuming video. The connection remains open across video
renegotiation and sends `display-ping` at least every five seconds. Admission
expires after twenty seconds without a display request/heartbeat. Clipboard uses
a separate TLS connection with the same certificate identity.

1. Send `{"type":"session-status","sessionTakeover":1}`.
2. Idle: host atomically reserves admission and sends
   `{"type":"session-state","busy":false,"admitted":true}`. This is a lease,
   not an informational idle snapshot. Start display negotiation/video only now.
3. Occupied: host sends `{"type":"session-state","busy":true,"admitted":false,
   "challenge":"opaque-token","expiresInMs":30000}`. Ask the user whether to
   disconnect the previous device. Closing this connection cancels without
   affecting the previous stream. Never auto-confirm, even for the same identity.
4. On explicit confirmation, send `{"type":"session-takeover","challenge":"opaque-token"}`
   on the same connection within 30 seconds. Wait up to 25 seconds for completion.
5. Only `{"type":"session-result","admitted":true}` authorizes starting video.
   Failure is `{"type":"session-result","admitted":false,"code":"stale|busy|unavailable|unauthorized",
   "error":"human-readable explanation"}`. Retry requires a fresh status query
   and, when occupied, a new explicit confirmation.

A challenge belongs to its TLS connection, certificate and observed host session
revision. Every confirmation attempt consumes it. A changed session, expired or
replayed token, concurrent operation or revoked binding cannot authorize eviction.
An admitted connection may repeat status without losing its lease. A second
connection from that same certificate is still a distinct contender.

Before reporting takeover success, the host fences old/pending video starts,
stops and joins the previous Sunshine stream(s), releases their input contexts,
closes old clipboard/display controls, and waits for display restoration. Failure
must not authorize a new stream. A completed eviction cannot be rolled back if
the new client disconnects or restoration fails; the temporary reservation is
released. Never restart the host process as a substitute for stream termination.

An opted-in old control connection receives
`{"type":"session-ended","reason":"taken-over"}` and then closes. The viewer
must release input and stop video on that message or on admitted-control loss.

## Compatibility and trust boundaries

Do not send optional messages to a host without the capability. Old host behavior
remains available only before capability negotiation. Once advertised/negotiated,
any admission, resize or control-loss failure is fatal for the stream; fixed-size
fallback must never bypass admission. Legacy viewers may lack an explanation,
but the host must stop their actual video stream on confirmed takeover.

The management adapter uses an authenticated, certificate-pinned loopback API.
Sunshine compares a session snapshot and claims a certificate-bound lease under
one mutex shared with authenticated launch/resume/cancel and final RTSP admission.
Generation checks reject pending negotiations from before an ownership change;
a single stream is admitted at a time. Lease release is conditional on its opaque
ID so late cleanup cannot release a newer reservation. Pairing/trust remains
unchanged. The management API is not a public client protocol.

`session-cases.json` enumerates the production host TLS contract scenarios. Native
adapters should also test unsupported old hosts, explicit cancel/accept UI, fatal
post-opt-in failure, and retained admission across video-only rotation/restart.
