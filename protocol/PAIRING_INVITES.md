# One-time mobile pairing invitations

2026-10-04. Optional extension to [SPEC.md](SPEC.md). The baseline remains
version 1. Native adapters own URI parsing, TLS, secure random generation,
storage, terminal rendering and user interaction. This contract introduces no
workspace, display, media or licensing policy change.

## Operator invitation

A local, same-user host management command creates one invitation for an
explicit reachable connection entry. It never guesses the public/NAT address.
An omitted port uses the active binding listener, not a streaming-port offset.
An invitation is host-side approval for exactly one client-only binding. It is
not a permanent auto-approve setting or a mutual-desktop invitation.

The URI is `deskport://bind` with exactly six query fields:

| Field | Value |
| --- | --- |
| `v` | `1` |
| `entry` | ASCII DNS name (at most 253 bytes), IPv4, or bracketed IPv6, followed by an explicit decimal TCP port 1..65535 without leading zeros |
| `id` | Host UUID, canonical lowercase hyphenated form, nonzero |
| `fp` | Lowercase 64-character SHA-256 hex of the binding TLS leaf certificate DER |
| `token` | 32 cryptographically random bytes, canonical base64url without padding (43 characters) |
| `exp` | Expiry as a positive decimal Unix timestamp in whole seconds, no leading zeros |

Percent-encode query values, including the entry's colon/brackets. Reject
duplicate, unknown or missing fields, unsupported versions, malformed percent
escapes, whitespace/control characters, userinfo, unexpected paths/fragments,
and URIs longer than 2048 UTF-8 bytes. The entry contains no path, query,
fragment, scheme or credentials; DNS names use ASCII hostname syntax, and IPv6
zone identifiers are not accepted. The fingerprint is the binding certificate,
not the streaming certificate. Names come from the verified TLS hello rather
than the QR payload. The port identifies the configured reachable entry;
advertised internal binding ports must not replace a forwarded entry.

An invitation lasts 300 seconds. Clients require `now < exp <= now + 330`
(30 seconds of forward clock tolerance), including immediately before the
confirmed request. Host expiry is authoritative and must resist wall-clock
rollback by also enforcing a monotonic deadline. A new invitation replaces the
old one; explicit revocation and process restart invalidate it. Store the token
only in memory. Do not include it in normal status, diagnostics or peer records.
The terminal QR and explicit JSON/link output necessarily contain this bearer
secret. Terminal output includes its expiry and explains that it grants access.

## Preview and confirmation

An invitation-capable host advertises `hello.meta.pairingInvite: 1`. An app
launch from a link only starts a read-only preview:

1. Parse the bounded URI and reject expired or malformed invitations.
2. Establish TLS with the normal client identity. Verify the leaf DER hash
   against `fp` before accepting application data. Existing saved pins must also
   match; an invitation cannot replace a saved host identity.
3. Validate the normal hello, `id`, usable streaming certificate/endpoints,
   and `pairingInvite: 1`. Show the verified host name, configured entry and
   binding certificate fingerprint in an explicit Bind/Cancel confirmation.

Preview sends no `request`, grants no access, starts no stream, writes no saved
route, endpoint, certificate or device, and does not occupy the host's pending
binding slot. A valid hello verifies the connection and host identity; it does
not prove that the token is still active. Cancellation or app interruption before
confirmation leaves no binding. Do not persist invitation links in app state,
intent history or logs beyond the in-memory operation.

Only a user tap on Bind may reconnect with the same UUID and fingerprint and
send the normal client-only request plus `inviteToken`:

```json
{"type":"request","tx":"<uuid>","inviteToken":"<token>","meta":{"version":1,"clientBinding":1,"role":"client","name":"<client name>"}}
```

The host first validates client metadata, transaction, request state, readiness
and its normal busy gate. Then it validates the token and atomically consumes it
before sending approval or mutating trust. Wrong, revoked, expired or replayed
tokens fail closed; a present but invalid `inviteToken` never falls back to
manual approval. A host-role/mutual request cannot consume an invitation.
Invalid or busy requests do not consume a valid invitation. No second host UI
approval is needed because the local operator issued the invitation.

The remainder is the existing
`pending -> accept -> ready -> client-ready -> bound` exchange, with the same
TLS client-certificate authorization. `client-ready` still means the client has
saved its binding. Failures after confirmation can leave a partial binding, as
with ordinary approval; do not claim a distributed transaction or silently
restore a consumed token. Report failure and allow a fresh operator invitation
or normal saved-device removal/recovery. Binding success saves the device but
does not automatically start streaming.

## Compatibility and verification

Manual requests without `inviteToken` retain the existing explicit host approval
flow, whether or not an invitation exists. New clients refuse QR binding to a
host without the capability. There is no downgrade to unpinned discovery.
Old clients ignore the optional hello field and continue manual binding.

`pairing-invite-cases.json` contains shared URI fixtures with a fixed clock.
Each invalid case names the single rule its `reason` exercises; the reference
parser in `tests/test_pairing_invites.py` checks those reasons in order (length,
URI shape, fields, escapes, then each value). Consumers only need to reject.
Because every value is bounded, no otherwise valid URI reaches 2048 bytes: the
length limit is a pre-parse bound that must be checked before decoding.
Native transport tests must also exercise wrong certificate/UUID, missing
capability, preview/cancel without writes, entry preservation, confirmation,
expiry at confirmation, duplicate delivery, saved-pin conflicts, replay,
revocation/replacement, concurrent requests and failed authorization. Decode an
actual rendered terminal QR back to its exact URI. App scheme dispatch and
confirmation UI need cold/warm launch checks on iOS and Android. Custom schemes
may show an app chooser or be unsupported by a camera; verified HTTPS app links
need separately configured website associations. A development deep-link test
does not establish physical-camera or streaming acceptance.
