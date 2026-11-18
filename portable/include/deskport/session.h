// SPDX-License-Identifier: MIT
#ifndef DESKPORT_PORTABLE_SESSION_H
#define DESKPORT_PORTABLE_SESSION_H

#include <math.h>
#include "workspace.h"

/* These are predicates on already parsed fields, not protocol state machines.
 * JSON adapters must reject wrong types (including boolean-as-number), absent
 * required fields and errors before calling. Authentication facts are supplied
 * only after the native adapter verifies them. No predicate acquires a lease. */
static inline int dp_session_reply_valid(int busy, int admitted) {
    return dp_contract_boolean_valid(busy) && dp_contract_boolean_valid(admitted) &&
           !(busy && admitted);
}

typedef enum {
    DP_SESSION_INVALID = -1, DP_SESSION_REJECTED = 0,
    DP_SESSION_OCCUPIED = 1, DP_SESSION_ADMITTED = 2
} DPSessionReply;

static inline int dp_session_reply_state(int busy, int admitted) {
    if (!dp_session_reply_valid(busy, admitted)) return DP_SESSION_INVALID;
    return admitted ? DP_SESSION_ADMITTED : (busy ? DP_SESSION_OCCUPIED : DP_SESSION_REJECTED);
}

static inline int dp_session_takeover_allowed(int confirmed, int same_connection, int current_challenge) {
    return confirmed == 1 && same_connection == 1 && current_challenge == 1;
}

static inline int dp_resume_resize_allowed(int same_authenticated_peer, int token_matches,
                                           int reservation_matches, int resumed) {
    return same_authenticated_peer == 1 && token_matches == 1 &&
           reservation_matches == 1 && resumed == 1;
}

/* Display correlation is exact; it imposes no new monotonic request rule. */
static inline int dp_display_result_valid(int64_t pending_seq, int64_t result_seq,
                                           DPWorkspace requested, int width, int height,
                                           int has_error) {
    return has_error == 0 && dp_contract_sequence_valid(pending_seq) &&
           result_seq == pending_seq && dp_workspace_valid(requested) &&
           width == requested.width && height == requested.height;
}

static inline int dp_pause_result_valid(int64_t pending_seq, int64_t result_seq,
                                         int requested, int observed, int has_error) {
    return has_error == 0 && dp_contract_sequence_valid(pending_seq) &&
           result_seq == pending_seq && dp_contract_boolean_valid(requested) && observed == requested;
}

typedef enum {
    DP_RATE_ACK_TERMINATE = 0, DP_RATE_ACK_APPLIED = 1, DP_RATE_ACK_RESTART = 2
} DPRateAck;

/* Each channel's own pending sequence is passed separately. Saver presence and
 * echo are checked when used; older hosts may omit it. Missing ack: terminate. */
static inline int dp_rate_result(int64_t pending_seq, int64_t result_seq,
                                  int requested_kbps, int observed_kbps, int live,
                                  int has_error) {
    if (has_error != 0 || !dp_contract_sequence_valid(pending_seq) || result_seq != pending_seq ||
        !dp_contract_rate_valid(requested_kbps) || observed_kbps != requested_kbps ||
        !dp_contract_boolean_valid(live)) return DP_RATE_ACK_TERMINATE;
    return live ? DP_RATE_ACK_APPLIED : DP_RATE_ACK_RESTART;
}

/* Opaque local generation IDs come from the adapter, never from untrusted
 * event claims. A new lease or controller changes the active generation. */
static inline int dp_event_in_scope(int admitted, int opted_in,
                                     uint64_t active_generation, uint64_t event_generation) {
    return admitted == 1 && opted_in == 1 && active_generation != 0 &&
           active_generation == event_generation;
}

static inline int dp_caret_valid(int in_scope, int valid, double x, double y) {
    return in_scope == 1 && valid == 1 && isfinite(x) && isfinite(y) &&
           x >= 0 && x <= 1 && y >= 0 && y <= 1;
}
#endif
