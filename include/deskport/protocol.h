// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef DESKPORT_PROTOCOL_H
#define DESKPORT_PROTOCOL_H
#include <stdint.h>
#include <string.h>
#include "../../portable/include/deskport/catalog.h"
// Shared wire names and bounded validators. Transport, TLS and JSON parsing stay
// in consumer adapters; callers must reject non-integral JSON values before using
// the integer validators below.
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
#define DP_VIDEO_PAUSE_VERSION 1
#define DP_MESSAGE_VIDEO_STATE "video-state"
#define DP_MESSAGE_VIDEO_RESULT "video-result"
#define DP_SESSION_LIFECYCLE_VERSION 1
#define DP_MESSAGE_SESSION_RELEASE "session-release"

// Optional Seamless / App Mode. Omission of the capability or sessionMode keeps
// the legacy Desktop Mode path. A peer must never infer Seamless Mode from a
// message name or silently downgrade an explicit Seamless request to Desktop.
#define DP_SEAMLESS_PROTOCOL_VERSION 1
#define DP_SEAMLESS_CAPABILITY "seamlessMode"
#define DP_SEAMLESS_VERSION_FIELD "seamlessVersion"
#define DP_SESSION_MODE_FIELD "sessionMode"
#define DP_SESSION_MODE_DESKTOP "desktop"
#define DP_SESSION_MODE_SEAMLESS "seamless"
#define DP_MESSAGE_SEAMLESS_NEGOTIATE "seamless-negotiate"
#define DP_MESSAGE_SEAMLESS_RESULT "seamless-result"

// Every Seamless control message is prefixed so a Desktop handler cannot confuse
// it with an existing display or GameStream message. WINDOW_DESTROY is an
// authoritative server event; WINDOW_CLOSE is only a client request.
#define DP_MESSAGE_SEAMLESS_WINDOW_CREATE "seamless-window-create"
#define DP_MESSAGE_SEAMLESS_WINDOW_DESTROY "seamless-window-destroy"
#define DP_MESSAGE_SEAMLESS_WINDOW_TITLE "seamless-window-title"
#define DP_MESSAGE_SEAMLESS_WINDOW_RESIZE_REQUEST "seamless-window-resize-request"
#define DP_MESSAGE_SEAMLESS_WINDOW_RESIZE_RESULT "seamless-window-resize-result"
#define DP_MESSAGE_SEAMLESS_WINDOW_CLOSE "seamless-window-close"
#define DP_MESSAGE_SEAMLESS_WINDOW_CURSOR "seamless-window-cursor"
#define DP_MESSAGE_SEAMLESS_WINDOW_FOCUS "seamless-window-focus"
#define DP_MESSAGE_SEAMLESS_INPUT_POINTER "seamless-input-pointer"
#define DP_MESSAGE_SEAMLESS_INPUT_KEYBOARD "seamless-input-keyboard"
#define DP_MESSAGE_SEAMLESS_PROTOCOL_ERROR "seamless-protocol-error"
#define DP_SEAMLESS_ERROR_UNSUPPORTED_VERSION "unsupported-version"
#define DP_SEAMLESS_ERROR_MODE_NOT_ADVERTISED "mode-not-advertised"
#define DP_SEAMLESS_ERROR_WRONG_SESSION_MODE "wrong-session-mode"
#define DP_SEAMLESS_ERROR_INVALID_MESSAGE "invalid-message"
#define DP_SEAMLESS_ERROR_CONTROL_TOO_LARGE "control-too-large"
#define DP_SEAMLESS_ERROR_TOO_MANY_WINDOWS "too-many-windows"
#define DP_SEAMLESS_ERROR_DUPLICATE_WINDOW_ID "duplicate-window-id"
#define DP_SEAMLESS_ERROR_UNKNOWN_WINDOW_ID "unknown-window-id"
#define DP_SEAMLESS_ERROR_INVALID_WINDOW_SIZE "invalid-window-size"
#define DP_SEAMLESS_ERROR_MEDIA_NOT_NEGOTIATED "media-not-negotiated"
#define DP_SEAMLESS_ERROR_FRAME_TOO_LARGE "frame-too-large"

// Numeric identifiers fit signed 32-bit consumer APIs and JSON integers exactly.
// Zero is invalid and an identifier is never reused during one admitted session.
#define DP_SEAMLESS_WINDOW_ID_MIN UINT32_C(1)
#define DP_SEAMLESS_WINDOW_ID_MAX UINT32_C(2147483647)
#define DP_SEAMLESS_SEQUENCE_MIN UINT32_C(1)
#define DP_SEAMLESS_SEQUENCE_MAX UINT32_C(2147483647)
#define DP_SEAMLESS_MAX_ACTIVE_WINDOWS 64

// Sizes are backing pixels. Surface sizes need not use Desktop Mode's four-pixel
// alignment; an encoder may pad internally but must preserve the visible size.
#define DP_SEAMLESS_WINDOW_MIN_WIDTH 16
#define DP_SEAMLESS_WINDOW_MIN_HEIGHT 16
#define DP_SEAMLESS_WINDOW_MAX_WIDTH 7680
#define DP_SEAMLESS_WINDOW_MAX_HEIGHT 4320
#define DP_SEAMLESS_WINDOW_TITLE_LIMIT 1024
#define DP_SEAMLESS_APP_ID_LIMIT 255

// Control remains bounded newline JSON. Encoded media belongs on a separately
// negotiated binary channel and is bounded before allocation or decode.
#define DP_SEAMLESS_CONTROL_FRAME_LIMIT DP_PROTOCOL_CONTROL_BUFFER_LIMIT
#define DP_SEAMLESS_ENCODED_FRAME_LIMIT UINT32_C(33554432)

typedef enum DPSeamlessMediaKind {
    DP_SEAMLESS_MEDIA_FRAME = 1,
    DP_SEAMLESS_MEDIA_DAMAGE = 2
} DPSeamlessMediaKind;

static inline int dp_session_mode_is_desktop(const char *mode) {
    return mode == 0 || strcmp(mode, DP_SESSION_MODE_DESKTOP) == 0;
}
static inline int dp_seamless_preflight_valid(const char *mode, int capability_version,
                                              int requested_version) {
    return mode != 0 && strcmp(mode, DP_SESSION_MODE_SEAMLESS) == 0 &&
        capability_version == DP_SEAMLESS_PROTOCOL_VERSION &&
        requested_version == DP_SEAMLESS_PROTOCOL_VERSION;
}
static inline int dp_seamless_window_id_valid(uint64_t identifier) {
    return identifier >= DP_SEAMLESS_WINDOW_ID_MIN && identifier <= DP_SEAMLESS_WINDOW_ID_MAX;
}
static inline int dp_seamless_sequence_valid(uint64_t sequence) {
    return sequence >= DP_SEAMLESS_SEQUENCE_MIN && sequence <= DP_SEAMLESS_SEQUENCE_MAX;
}
static inline int dp_seamless_window_size_valid(int width, int height) {
    return width >= DP_SEAMLESS_WINDOW_MIN_WIDTH && width <= DP_SEAMLESS_WINDOW_MAX_WIDTH &&
        height >= DP_SEAMLESS_WINDOW_MIN_HEIGHT && height <= DP_SEAMLESS_WINDOW_MAX_HEIGHT;
}
static inline int dp_seamless_damage_rect_valid(int x, int y, int width, int height,
                                                int window_width, int window_height) {
    return dp_seamless_window_size_valid(window_width, window_height) &&
        x >= 0 && y >= 0 && width > 0 && height > 0 &&
        x <= window_width && y <= window_height &&
        width <= window_width - x && height <= window_height - y;
}
static inline int dp_seamless_control_frame_size_valid(uint64_t bytes) {
    return bytes > 0 && bytes <= DP_SEAMLESS_CONTROL_FRAME_LIMIT;
}
static inline int dp_seamless_encoded_frame_size_valid(uint64_t bytes) {
    return bytes > 0 && bytes <= DP_SEAMLESS_ENCODED_FRAME_LIMIT;
}

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
