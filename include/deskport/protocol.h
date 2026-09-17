// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef DESKPORT_PROTOCOL_H
#define DESKPORT_PROTOCOL_H
// Existing wire names only. This header does not introduce a new protocol version.
#define DP_PROTOCOL_BINDING_VERSION 1
#define DP_PROTOCOL_DEFAULT_BINDING_PORT 48991
#define DP_PROTOCOL_CONTROL_BUFFER_LIMIT 32768
#define DP_MESSAGE_DISPLAY_RESIZE "display-resize"
#define DP_MESSAGE_DISPLAY_RESULT "display-result"
#define DP_MESSAGE_DISPLAY_PING "display-ping"
#define DP_MESSAGE_DISPLAY_PONG "display-pong"
#define DP_MESSAGE_TEXT_CARET "text-caret"
// Optional, explicitly advertised per-session topology policy.
#define DP_DISPLAY_POLICY_VERSION 1
typedef enum DPDisplayPolicy {
    DP_DISPLAY_PRIMARY_MIRROR = 0,
    DP_DISPLAY_PRIMARY_ONLY = 1,
    DP_DISPLAY_EXTEND = 2
} DPDisplayPolicy;
static inline int DPDisplayPolicyValid(int policy) {
    return policy >= DP_DISPLAY_PRIMARY_MIRROR && policy <= DP_DISPLAY_EXTEND;
}
#endif
