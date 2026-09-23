# Optional desktop session lifecycle

Version 1 is negotiated independently of binding and display policy.

- `hello.meta.clientWindow = 1`: host can send `client-window` with
  `action: leave-fullscreen` only after the approved display controller opts in
  using `display-resize.clientWindow = 1`. This exits full screen and releases
  input without disconnecting; a client that has not opted in receives no event.
  An opted-in client also sends `display-resize.clientFullScreen` (boolean) with
  every resize. Entering or leaving full screen changes the window, so each change
  is followed by a resize and the host always knows the current state. The host
  offers the request only while the last report is `true`; a request without the
  field (older clients) keeps it available. Hosts never ask a client to enter
  full screen. Desktop clients leave window full screen; mobile clients show their
  session bar again and renegotiate the smaller area.
- `hello.meta.sessionLifecycle = 1`: a client opts in with
  `session-status.sessionLifecycle = 1`. Admission returns `resumeToken`, a
  random, session-scoped secret. It must not be logged or persisted.
- A dropped controller has a 15-second grace period. Only a controller with the
  same pinned client certificate and matching token may resume the lease using
  `session-status.resumeToken`. This does not authorize takeover. New identities,
  invalid tokens and expired leases use normal explicit admission.
- `session-release` from the admitted lifecycle controller ends ownership and
  restores/releases its display immediately. EOF from older clients retains the
  existing immediate-release behavior. Revocation, takeover and invalid protocol
  are terminal and must not enter grace or trigger automatic takeover.
- Desktop recovery is bounded to 30 seconds with 1/2/4-second backoff, cancellation
  and no automatic takeover. Once grace expires a reconnect may acquire an idle
  host, but cannot evict another session. A stable stream resets retry history.
- A matching identity/token may replace its prior transport before the old TCP
  EOF arrives (for example after a route change). The old transport is closed;
  its display snapshot and reservation are transferred, never duplicated.
