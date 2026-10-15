# Optional live video bitrate ceiling, version 1

A host advertises `videoRate: 1` in hello metadata. A viewer opts in with
`videoRate: 1` on session-status before admission. Absent capability means the
negotiated bitrate is fixed for the stream; viewers must not send unknown
messages to older hosts and change their ceiling by reconnecting instead.
Existing takeover, topology, binding and TLS checks remain mandatory.

On the admitted display TLS connection, `video-rate` carries a positive integral
`seq` and an integral `ceilingKbps` from 500 to 200000. Sequences start at 1 per
connection and are independent of `video-state`. Only one command may be
outstanding. `video-rate-result` echoes `seq` and `ceilingKbps` and adds a
boolean `live`; an `error` means failure. An exact completed duplicate returns the
cached result. Conflicting duplicates, out-of-order sequences, malformed fields
and requests from other connections fail.

`ceilingKbps` is in the same units as the bitrate the viewer requested when the
stream started (before the host deducts FEC, audio and packet overhead). The
host scales its encoder target by `min(1, ceilingKbps / requested)`; a ceiling at
or above the requested bitrate removes the cap. It never raises the encoder above
the negotiated rate, never changes resolution, and does not request a key frame.
Host congestion control may still lower the bitrate below the ceiling.

`live: true` means the encoder accepted the new rate for the running stream.
`live: false` means the ceiling was recorded but the encoder cannot change rate
while streaming; the viewer then applies the change by reconnecting, as it would
without the capability. The ceiling applies to the current admitted lease only;
a newly admitted lease starts uncapped unless its launch request carries one.
A failed or missing acknowledgment (12 second client deadline) ends the control
operation like `video-state`; it must not be reported as applied.

Required checks: negotiation and legacy fallback; malformed, out-of-range,
duplicate and stale commands; ownership and takeover fencing; `live: false`
fallback to reconnect; repeated toggles; no key frame on a change.
