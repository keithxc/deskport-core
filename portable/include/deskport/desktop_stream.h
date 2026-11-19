// SPDX-License-Identifier: MIT
#ifndef DESKPORT_PORTABLE_DESKTOP_STREAM_H
#define DESKPORT_PORTABLE_DESKTOP_STREAM_H

#include <stdint.h>
#include "contracts.h"

#define DP_DESKTOP_SAVER_FPS 8

/* Independently expressed desktop product formula: the contract's reference
 * kbps per pixel-frame, with dimensions/fps floored at one and fps capped.
 * Quantize to whole kbps before applying the full-chroma factor, then clamp.
 * Bound the numerator before multiplying so even INT_MAX geometry is safe. */
static inline int dp_desktop_bitrate_automatic(int width, int height, int fps, int full_chroma) {
    const uint64_t area = (uint64_t)(width > 0 ? width : 1) * (uint64_t)(height > 0 ? height : 1);
    const int cadence = fps < 1 ? 1 : (fps > DP_BITRATE_MAX_FPS ? DP_BITRATE_MAX_FPS : fps);
    const uint64_t unit = (uint64_t)DP_BITRATE_BASE_WIDTH * DP_BITRATE_BASE_HEIGHT * DP_BITRATE_BASE_FPS;
    const uint64_t weight = (uint64_t)cadence * DP_BITRATE_BASE_KBPS;
    if (area > (uint64_t)DP_BITRATE_AUTO_MAX_KBPS * unit / weight) return DP_BITRATE_AUTO_MAX_KBPS;
    const uint64_t kbps = (area * weight / unit) * (full_chroma ? 2 : 1);
    return kbps < DP_BITRATE_AUTO_MIN_KBPS ? DP_BITRATE_AUTO_MIN_KBPS :
        (kbps > DP_BITRATE_AUTO_MAX_KBPS ? DP_BITRATE_AUTO_MAX_KBPS : (int)kbps);
}

/* Desktop saver uses the same pixel-frame price at an eight-frame cadence,
 * bounded to 500..4000 kbps. It does not divide an automatic estimate by four. */
static inline int dp_desktop_bitrate_saver(int width, int height) {
    const uint64_t area = (uint64_t)(width > 0 ? width : 1) * (uint64_t)(height > 0 ? height : 1);
    const uint64_t unit = (uint64_t)DP_BITRATE_BASE_WIDTH * DP_BITRATE_BASE_HEIGHT * DP_BITRATE_BASE_FPS;
    const uint64_t weight = (uint64_t)DP_DESKTOP_SAVER_FPS * DP_BITRATE_BASE_KBPS;
    if (area > UINT64_C(4000) * unit / weight) return 4000;
    const uint64_t kbps = area * weight / unit;
    return kbps < 500 ? 500 : (int)kbps;
}

#endif
