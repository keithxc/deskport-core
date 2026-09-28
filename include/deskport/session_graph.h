// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef DESKPORT_SESSION_GRAPH_H
#define DESKPORT_SESSION_GRAPH_H
#include <stddef.h>
#include <string.h>
#define DP_SESSION_TOPOLOGY_VERSION 1
#define DP_SESSION_PATH_MAX 16
#define DP_MESSAGE_SESSION_PATH "session-path"
#define DP_MESSAGE_SESSION_PATH_RESULT "session-path-result"
// Paths contain pinned binding-certificate SHA-256 identities, never hostnames.
static inline int dp_session_identity_valid(const char* identity) {
    if (!identity || strlen(identity) != 64) return 0;
    for (size_t i = 0; i < 64; ++i)
        if (!((identity[i] >= '0' && identity[i] <= '9') ||
              (identity[i] >= 'a' && identity[i] <= 'f'))) return 0;
    return 1;
}
// 0: append allowed; 1: cycle; 2: invalid/depth limit. Caller appends self.
static inline int dp_session_path_check(const char* const* path, size_t count, const char* self) {
    if (!count || count >= DP_SESSION_PATH_MAX || !dp_session_identity_valid(self)) return 2;
    for (size_t i = 0; i < count; ++i) {
        if (!dp_session_identity_valid(path[i])) return 2;
        if (strcmp(path[i], self) == 0) return 1;
        for (size_t j = 0; j < i; ++j) if (strcmp(path[i], path[j]) == 0) return 1;
    }
    return 0;
}
#endif
