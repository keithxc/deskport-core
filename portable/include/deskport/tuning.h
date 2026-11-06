// SPDX-License-Identifier: MIT
#ifndef DESKPORT_PORTABLE_TUNING_H
#define DESKPORT_PORTABLE_TUNING_H

#include "catalog.h"

/* Dimensions and tuning choices are bounded; cross products fit in signed 32 bits. */
typedef struct { int numerator, denominator; } DPTuningRatio;

static inline int dp_tuning_less(DPTuningRatio a, DPTuningRatio b) {
    return a.numerator * b.denominator < b.numerator * a.denominator;
}

static inline int dp_tuning_aligned(int extent, DPTuningRatio ratio) {
    int units = 4 * ratio.denominator;
    return 4 * ((extent * ratio.numerator + units - 1) / units);
}

/* Apply the zoom and the orientation-aware desktop floor to the original
 * aspect ratio. Quantize only the final dimensions, including at the floor. */
static inline int dp_tuned_desktop_size(int w, int h, int scale, double zoom,
                                        int *width, int *height) {
    *width = 0;
    *height = 0;
    if (w < 640 || w > 7680 || h < 360 || h > 4320 || w % 4 || h % 4 ||
        (scale != 1 && scale != 2)) return 0;
    DPTuningRatio ratio = {1, 1};
    for (int i = 0; i < DP_CATALOG_TUNING_COUNT; ++i) {
        double delta = zoom - dp_catalog_tuning_values[i];
        if (delta > -0.000001 && delta < 0.000001) {
            ratio.numerator = 10;
            ratio.denominator = (int)(10 * dp_catalog_tuning_values[i] + 0.5);
            break;
        }
    }
    int floor_w = (h > w ? 600 : 800) * scale;
    DPTuningRatio min_w = {floor_w < 640 ? 640 : floor_w, w};
    DPTuningRatio min_h = {(h > w ? 800 : 600) * scale, h};
    DPTuningRatio max_w = {7680, w}, max_h = {4320, h};
    DPTuningRatio lower = dp_tuning_less(min_w, min_h) ? min_h : min_w;
    DPTuningRatio upper = dp_tuning_less(max_w, max_h) ? max_w : max_h;
    if (dp_tuning_less(upper, lower)) return 0;
    if (dp_tuning_less(ratio, lower)) ratio = lower;
    if (dp_tuning_less(upper, ratio)) ratio = upper;
    *width = dp_tuning_aligned(w, ratio);
    *height = dp_tuning_aligned(h, ratio);
    return 1;
}
#endif
