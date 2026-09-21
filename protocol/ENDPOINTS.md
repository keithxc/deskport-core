# Stable connection entry and streaming endpoints

2026-09-21: Desktop and mobile clients use an independent connection entry,
default TCP 48991. An explicit entry can be any TCP port from 1 to 65535.
Streaming HTTP ports retain the catalog port family; media offsets do not
identify the connection entry.

The TLS hello advertises version 1, endpointRefresh 1, hostId, hostCert,
hostPort and bindingPort. Initial discovery can inspect this unapproved hello,
but must not treat it as authorization. Pairing pins the TLS identity and
streaming certificate and verifies the selected UUID. The requested entry is
retained even when the advertised bindingPort differs (for example forwarding).

An approved client reconnects with its client TLS certificate and pinned server
TLS certificate, validates the hello UUID and streaming certificate, sends
`{"type":"endpoint-query"}`, and accepts only a validated endpoint-result meta.
The host rejects revoked or unapproved certificates. A hello alone must never
refresh an approved device's endpoint. A failed authenticated refresh fails
closed; it must not silently use stale addresses or try a guessed listener.

Persist the user entry separately from negotiated streaming endpoints and the
advertised binding port. Refresh may replace only the negotiated endpoint of an
unchanged record. Compare the entry, revision, TLS pin and streaming identity
against the request snapshot, so edits, deletion and revocation cannot be undone.
Historical mobile stream-address overrides migrate their hostname to default
entry 48991, preserving the old record. Do not reinterpret the old numeric port
as an explicit control entry. New explicit entries are never migrated.

Required cases: unequal ports, arbitrary custom entry, changed stream port,
retained reachable old/forwarded entry, first binding, reconnect, wrong TLS pin,
wrong UUID, wrong stream certificate, revoked client and concurrent local edits.
