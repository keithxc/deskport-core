# Optional video transmission pause, version 1

A host advertises `videoPause: 1` in hello metadata. A viewer opts in with
`videoPause: 1` on session-status before admission. Absent capability means
continuous video; viewers must not send unknown messages to older hosts.
Existing takeover, topology, binding and TLS checks remain mandatory.

On the admitted display TLS connection, `video-state` carries a positive integral
`seq` and boolean `paused`. Sequences start at 1 per connection. Only one command
may be outstanding. `video-result` echoes both fields; an `error` means failure.
An exact completed duplicate returns the cached result. Conflicting duplicates,
out-of-order sequences, malformed fields and requests from other connections fail.
Native adapters coalesce presentation changes to the latest desired boolean.

Pause stops video UDP sends at the server. Acknowledgment follows the last send;
packets already in the network may still arrive. The display lease, RTSP/media
session, control heartbeat and audio remain alive. Capture and encoding may
continue in version 1; this is not an encoder-suspension guarantee. Background
input must remain disabled independently of protocol support. Audio ownership is
not changed by this extension.

Resume discards queued packets created before the resume boundary, requests an
IDR, and suppresses non-IDR packets until a newly encoded key frame is available.
A static desktop may encode its retained captured image. Acknowledgment confirms
the send gate changed, not decoded-frame delivery or display latency.

Clients pause only after receiving a complete initial key frame. A failed or
missing acknowledgment (12 second client deadline, 10 second loopback deadline)
makes remote state uncertain and terminates the control operation; it must not
silently report success or reconnect as a pause mechanism. Admission loss follows
the existing lifecycle cleanup. A newly admitted lease resets the gate. Lease
checks and gate mutations are serialized against takeover; old lease commands
cannot affect the replacement stream.

Required checks: negotiation and legacy fallback; malformed, duplicate and stale
commands; ownership and takeover fencing; frame-send counters while paused;
new key frames after resume; rapid desired-state changes; long pause with
heartbeats; independent disconnect; and uncertain-state failure handling.
