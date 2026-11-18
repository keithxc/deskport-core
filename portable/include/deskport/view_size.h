// SPDX-License-Identifier: MIT
#ifndef DESKPORT_PORTABLE_VIEW_SIZE_H
#define DESKPORT_PORTABLE_VIEW_SIZE_H

#include <math.h>

/* Input is the usable logical rectangle after system insets. The return
 * value is the negotiated backing scale; zero means defer the size request. */
static inline int dp_view_workspace(double w, double h, double density, int *width, int *height) {
    *width = *height = 0;
    if (!isfinite(w) || !isfinite(h) || !isfinite(density) ||
        w < 128 || h < 128 || density < 0.5 || density > 8) return 0;

    /* Fit the requested backing resolution in the protocol box with a single
     * aspect-preserving multiplier. Normalize first to bound arithmetic. */
    int backing = density > 1 ? 2 : 1;
    double longest = fmax(w, h);
    double x = w / longest, y = h / longest;
    double min_edge = fmax(640 / x, 360 / y);
    double max_edge = fmin(7680 / x, 4320 / y);
    double edge = fmin(max_edge, fmax(min_edge, longest * backing));
    double preferred = longest * backing;
    double exact_w = edge == preferred ? w * backing : x * edge;
    double exact_h = edge == preferred ? h * backing : y * edge;
    int pixels_w = (int)fmin(7680, 4 * ceil(exact_w / 4));
    int pixels_h = (int)fmin(4320, 4 * ceil(exact_h / 4));
    if (pixels_w < 640 || pixels_h < 360) return 0;
    *width = pixels_w;
    *height = pixels_h;
    return backing;
}

/* A conservative, even-sized video fallback for stream-only peers. */
static inline void dp_view_video(double w, double h, int *width, int *height) {
    *width = 1280;
    *height = 720;
    if (!isfinite(w) || !isfinite(h) || w < 128 || h < 128) return;
    double longest = fmax(w, h);
    if (longest > 1920) {
        w = w / longest * 1920;
        h = h / longest * 1920;
    }
    *width = (int)fmax(2, 2 * floor(w / 2));
    *height = (int)fmax(2, 2 * floor(h / 2));
}
#endif
