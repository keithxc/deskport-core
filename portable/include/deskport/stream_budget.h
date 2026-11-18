// SPDX-License-Identifier: MIT
#ifndef DESKPORT_PORTABLE_STREAM_BUDGET_H
#define DESKPORT_PORTABLE_STREAM_BUDGET_H

#include <math.h>
#include <stdint.h>
#include "contracts.h"

/* Positive geometry and finite positive fps are required. Cap fps at the product
 * maximum, then clamp the bitrate before any floating-to-integer cast. */
static inline int dp_bitrate_automatic(int width, int height, double fps, int full_chroma) {
    if (width <= 0 || height <= 0 || !isfinite(fps) || fps <= 0 ||
        !dp_contract_boolean_valid(full_chroma)) return 0;
    if (fps > DP_BITRATE_MAX_FPS) fps = DP_BITRATE_MAX_FPS;
    double rate = (double)width / DP_BITRATE_BASE_WIDTH * ((double)height / DP_BITRATE_BASE_HEIGHT) *
                  (fps / DP_BITRATE_BASE_FPS) * DP_BITRATE_BASE_KBPS * (full_chroma ? 2 : 1);
    if (rate >= DP_BITRATE_AUTO_MAX_KBPS) return DP_BITRATE_AUTO_MAX_KBPS;
    if (rate <= DP_BITRATE_AUTO_MIN_KBPS) return DP_BITRATE_AUTO_MIN_KBPS;
    return (int)rate;
}

/* Takes an automatic estimate, never a user cap. Zero is invalid, not a cap. */
static inline int dp_bitrate_saver(int automatic_kbps) {
    if (automatic_kbps <= 0) return 0;
    int cap = automatic_kbps / 4;
    return cap < DP_BITRATE_SAVER_MIN_KBPS ? DP_BITRATE_SAVER_MIN_KBPS :
        (cap > DP_BITRATE_SAVER_MAX_KBPS ? DP_BITRATE_SAVER_MAX_KBPS : cap);
}

/* Nonpositive manual means automatic. A positive manual cap is retained within
 * wire bounds; the saver estimate is always derived from automatic geometry. */
static inline int dp_bitrate_normal(int automatic_kbps, int manual_kbps) {
    if (manual_kbps > 0) return manual_kbps < DP_RATE_MIN_KBPS ? DP_RATE_MIN_KBPS :
        (manual_kbps > DP_RATE_MAX_KBPS ? DP_RATE_MAX_KBPS : manual_kbps);
    return automatic_kbps > 0 && dp_contract_rate_valid(automatic_kbps) ? automatic_kbps : 0;
}

static inline int dp_bitrate_effective(int automatic_kbps, int manual_kbps, int saver) {
    if (!dp_contract_boolean_valid(saver)) return 0;
    int normal = dp_bitrate_normal(automatic_kbps, manual_kbps);
    if (!saver || !normal) return normal;
    int cap = dp_bitrate_saver(automatic_kbps);
    return cap && cap < normal ? cap : (cap ? normal : 0);
}

/* Live capability alone is insufficient: the adapter supplies an admitted,
 * negotiated live-rate lease. Keep its normal ceiling for later saver off. */
static inline int dp_bitrate_start(int automatic_kbps, int manual_kbps, int saver,
                                    int admitted_live_rate) {
    if (!dp_contract_boolean_valid(saver) || !dp_contract_boolean_valid(admitted_live_rate)) return 0;
    return admitted_live_rate ? dp_bitrate_normal(automatic_kbps, manual_kbps) :
                               dp_bitrate_effective(automatic_kbps, manual_kbps, saver);
}

/* Use this at signed counter boundaries before conversion to unsigned bytes. */
static inline uint64_t dp_bytes_nonnegative(int64_t value) {
    return value < 0 ? 0 : (uint64_t)value;
}

static inline uint64_t dp_bytes_add(uint64_t total, uint64_t increment) {
    return increment > UINT64_MAX - total ? UINT64_MAX : total + increment;
}

/* First samples and counter resets count the current cumulative value, never
 * an unsigned wrap-around. Invalid presence flags return zero. No persistence. */
static inline uint64_t dp_bytes_delta(uint64_t previous, uint64_t current, int has_previous) {
    if (!dp_contract_boolean_valid(has_previous)) return 0;
    if (!has_previous) return current;
    return current >= previous ? current - previous : current;
}

typedef enum {
    DP_BUDGET_NORMAL = 0, DP_BUDGET_WARNING = 1,
    DP_BUDGET_CRITICAL = 2, DP_BUDGET_EXCEEDED = 3
} DPBudgetLevel;

/* ceil(limit * percent / 100), with each intermediate bounded by UINT64_MAX. */
static inline uint64_t dp_budget_threshold(uint64_t limit, unsigned percent) {
    if (percent > 100) return UINT64_MAX;
    return (limit / 100) * percent + ((limit % 100) * percent + 99) / 100;
}

/* A zero budget disables warning levels; exceeding a budget never stops media. */
static inline int dp_budget_level(uint64_t used, uint64_t limit) {
    if (!limit) return DP_BUDGET_NORMAL;
    if (used >= limit) return DP_BUDGET_EXCEEDED;
    if (used >= dp_budget_threshold(limit, 85)) return DP_BUDGET_CRITICAL;
    if (used >= dp_budget_threshold(limit, 70)) return DP_BUDGET_WARNING;
    return DP_BUDGET_NORMAL;
}
#endif
