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
#endif
