// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef DESKPORT_PROTOCOL_H
#define DESKPORT_PROTOCOL_H
#include "../../portable/include/deskport/catalog.h"
// Existing wire names only. This header does not introduce a new protocol version.
#define DP_PROTOCOL_BINDING_VERSION 1
#define DP_PROTOCOL_DEFAULT_BINDING_PORT (DP_CATALOG_BASE_PORT + DP_CATALOG_CONTROL_OFFSET)
#define DP_PROTOCOL_CONTROL_BUFFER_LIMIT 32768
#define DP_MESSAGE_DISPLAY_RESIZE "display-resize"
#define DP_MESSAGE_DISPLAY_RESULT "display-result"
#define DP_MESSAGE_DISPLAY_PING "display-ping"
#define DP_MESSAGE_DISPLAY_PONG "display-pong"
#define DP_MESSAGE_TEXT_CARET "text-caret"
// Optional admission on the long-lived display-control TLS connection.
#define DP_SESSION_TAKEOVER_VERSION 1
#define DP_SESSION_CONFIRMATION_TTL_MS 30000
#define DP_MESSAGE_SESSION_STATUS "session-status"
#define DP_MESSAGE_SESSION_STATE "session-state"
#define DP_MESSAGE_SESSION_TAKEOVER "session-takeover"
#define DP_MESSAGE_SESSION_RESULT "session-result"
#define DP_MESSAGE_SESSION_ENDED "session-ended"
#define DP_CLIENT_WINDOW_VERSION 1
#define DP_MESSAGE_CLIENT_WINDOW "client-window"
#define DP_SESSION_LIFECYCLE_VERSION 1
#define DP_MESSAGE_SESSION_RELEASE "session-release"
// Optional, explicitly advertised per-session topology policy.
#define DP_DISPLAY_POLICY_VERSION DP_CATALOG_DISPLAY_POLICY_VERSION
typedef enum DPDisplayPolicy {
    DP_DISPLAY_PRIMARY_MIRROR = DP_CATALOG_POLICY_PRIMARY_MIRROR,
    DP_DISPLAY_PRIMARY_ONLY = DP_CATALOG_POLICY_PRIMARY_ONLY,
    DP_DISPLAY_EXTEND = DP_CATALOG_POLICY_EXTEND
} DPDisplayPolicy;
static inline int DPDisplayPolicyValid(int policy) {
    return dp_catalog_display_policy_valid(policy);
}
#endif
