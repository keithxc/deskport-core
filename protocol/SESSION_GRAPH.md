# Acyclic active desktop sessions (sessionTopology 1)

Binding permission is bidirectional and does not create a graph edge. An edge
A -> B exists from A's connection reservation until its control object is joined
and released, including pending admission, takeover confirmation and media resize.
Every desktop identity is its pinned binding-certificate SHA-256 (64 lowercase hex).
Multiple transports of the same A -> B edge retain it until the last owner exits.
A second target for the same source is rejected until its existing edge is gone.

Before sending admission, a desktop publishes its pending edge in the same local
registry used by its host. A host advertises hello.meta.sessionTopology: 1;
updated desktops require this capability and sessionTakeover before starting video.
Every session-status includes sessionTopology: 1. Hosts reject desktop admission
without it. Existing explicitly client-only bindings remain compatible: they cannot
host an incoming return edge. This does not claim protection for independent old
applications or malicious peers which lie about implementing the capability.

Before admission and again before confirmed takeover, the host walks its outgoing
chain starting with the requesting certificate identity. Each hop validates the
path with dp_session_path_check, rejects self/repeated identities, appends self,
and forwards along its actual locally reserved outgoing edge. A missing edge is
a safe terminal. A session-path request runs over a fresh mutually authenticated,
pinned TLS connection between already granted adjacent peers; its final path
entry must match the immediate TLS client identity. Replies are only
session-path-result {safe: boolean, code: string}, not addresses or credentials.
An idle/stopped sharing service may still answer topology via its binding listener.

A maximum of 16 identities and a bounded probe deadline reject unknown paths.
Unsupported peers, EOF, invalid frames, timeouts and a changed local registry
revision fail closed (topology-unsupported/topology-unavailable). A detected
cycle returns cycle. Rejection never acquires a lease, evicts a stream or changes
a display. The same checks apply on transport recovery. No fixed-size or legacy
fallback may bypass this gate. Failed/cancelled probes do not mutate the graph.

Pending edges are visible before checks and remain visible until teardown. If a
set of additions would create a cycle, the last published edge in that cycle
checks after every edge in the cycle exists; it must find the cycle or fail closed.
An edge removed/re-added gets a new check, while a retained media restart keeps
its reservation. Per-hop revision validation rejects paths changed during a probe.
Simultaneous contenders can both fail and be retried; this intentionally favors
preserving current sessions over selecting a winner through destructive retries.

Adapter tests must exercise chains, reciprocal and three-node cycles, simultaneous
pending edges, takeover revalidation, stale reservation release, same-edge recovery,
unknown hops, old desktop rejection and client-only compatibility over real TLS.
