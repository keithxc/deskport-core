// SPDX-License-Identifier: GPL-3.0-or-later
// Extracted from DeskPort's workspace policy. No platform or transport dependencies.
#ifndef DESKPORT_WORKSPACE_H
#define DESKPORT_WORKSPACE_H
#include <math.h>

enum { DP_WORKSPACE_MAX_WIDTH = 7680, DP_WORKSPACE_MAX_HEIGHT = 4320 };
typedef struct { int width, height, scale; } DPWorkspace;

static inline int dp_workspace_valid(DPWorkspace size) {
    return size.width >= 640 && size.width <= DP_WORKSPACE_MAX_WIDTH &&
        size.height >= 360 && size.height <= DP_WORKSPACE_MAX_HEIGHT &&
        size.width % 4 == 0 && size.height % 4 == 0 &&
        (size.scale == 1 || size.scale == 2);
}

// Input is drawable pixels, NOT logical points. Scale is the client output density.
// This computes a proposal; callers must separately validate protocol eligibility.
// Extremely narrow aspect ratios can produce an ineligible proposal under the cap.
static inline DPWorkspace dp_workspace_from_pixels(double width, double height, double density) {
    DPWorkspace result = {0, 0, 0};
    if (!isfinite(width) || !isfinite(height) || !isfinite(density) ||
        width <= 0 || height <= 0 || density < 0.5 || density > 8) return result;
    const int scale = density > 1 ? 2 : 1;
    const double minimum = fmax(fmax(1.0, scale / density),
                               fmax(960.0 * scale / width, 540.0 * scale / height));
    const double maximum = fmin(DP_WORKSPACE_MAX_WIDTH / width, DP_WORKSPACE_MAX_HEIGHT / height);
    const double factor = fmin(minimum, maximum);
    result.width = (int)fmin(DP_WORKSPACE_MAX_WIDTH, ceil(width * factor / 4) * 4);
    result.height = (int)fmin(DP_WORKSPACE_MAX_HEIGHT, ceil(height * factor / 4) * 4);
    result.scale = scale;
    return result;
}
#endif
