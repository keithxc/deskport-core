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
