# Session display policy

2026-09-17: Add an optional topology policy to the existing authenticated,
exclusive display lease. Workspace pixel arithmetic is unchanged.

`hello.meta.displayPolicy = 1` advertises this contract. A supporting client sends
integer `displayPolicy` in every `display-resize` request. Values are:

| Value | Behavior |
| --- | --- |
| 0 (default) | Client workspace becomes primary; previously active displays mirror it. |
| 1 | Client workspace becomes primary; other previously active displays are disabled. |
| 2 | Client workspace extends the desktop; existing primary and layout remain intact. |

Missing policy means 0 for legacy clients. Unknown values, changing policy within
a lease, and unsupported policies must fail before changing display state. Clients
must not send the optional field to an unadvertised host; non-default choices must
fail explicitly rather than silently applying the legacy mirror policy.

Before the first mutation, persist one snapshot of all attached displays, including
stable identity, enabled state, primary, origin, mode, scale and mirror source.
Repeated resize requests and transport/video renegotiation never replace it.
Only displays active in that snapshot are mirror/disable targets. A display added
later is not silently captured. Extension does not reconfigure existing displays.

Restore on lease release/expiry, failed setup and helper shutdown. Restoration
uses stable identity, skips detached displays and retains the journal on failure.
Crash recovery runs before accepting another session. Successful configuration
submission alone does not prove that the OS has restored the topology: verify the
result before discarding the journal. No persistent system display preference is
written. Restoration is automatic, without a confirmation dialog; OS compositor
transitions may still be visible.

Native adapters own platform APIs and capability checks. A shared policy enum does
not imply Linux, Android or older host support.

## Local restoration and connection availability — 2026-09-17

A failed local-layout restoration must not permanently block a new authenticated
lease. Keep the original recovery journal, cancel idle restoration callbacks when
the new lease takes over, and independently verify the requested workspace's
capture target, pixel size and scale. Startup recovery is attempted before serving
new clients; a pending local restore is not by itself a reason to keep the host
offline. Never acknowledge an incorrect workspace mode as a successful resize.

When the workspace is verified but native primary/mirror/disable/layout operations
fail, prioritize the usable remote connection. Record the requested policy, the
original and observed display layouts, time and reason locally for manual repair.
Keep recovery pending for the next idle period. This is a local-layout degradation,
not permission to change the requested policy to another policy or resize an
unverified capture target. Unsupported policies and invalid requests still fail
before mutation. Native adapters may implement this recovery independently; older
adapters can still reject pending recovery until upgraded.
