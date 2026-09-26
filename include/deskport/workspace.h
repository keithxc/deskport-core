// SPDX-License-Identifier: GPL-3.0-or-later
// Extracted from DeskPort's workspace policy. No platform or transport dependencies.
#ifndef DESKPORT_WORKSPACE_H
#define DESKPORT_WORKSPACE_H
#include <math.h>
#include "../../portable/include/deskport/catalog.h"

enum { DP_WORKSPACE_MAX_WIDTH = 7680, DP_WORKSPACE_MAX_HEIGHT = 4320 };
typedef struct { int width, height, scale; } DPWorkspace;

static inline int dp_workspace_valid(DPWorkspace size) {
    return size.width >= 640 && size.width <= DP_WORKSPACE_MAX_WIDTH &&
        size.height >= 360 && size.height <= DP_WORKSPACE_MAX_HEIGHT &&
        size.width % 4 == 0 && size.height % 4 == 0 &&
        (size.scale == 1 || size.scale == 2);
}

// Select a finite host mode using relative size and aspect error. Empty lists
// preserve continuous sizing. Invalid lists fail closed rather than dropping
// a host constraint. Listed modes are physical pixels at scale 1.
static inline DPWorkspace dp_workspace_select_mode(DPWorkspace requested, const DPWorkspace *modes, int count) {
    const DPWorkspace empty = {0,0,0};
    if (!dp_workspace_valid(requested) || count < 0 || count > 96 || (count && !modes)) return empty;
    if (!count) return requested;
    DPWorkspace best=empty; double score=INFINITY;
    for (int i=0;i<count;++i) {
        if (!dp_workspace_valid(modes[i])) return empty;
        const double x=log((double)modes[i].width/requested.width);
        const double y=log((double)modes[i].height/requested.height);
        const double candidate=x*x+y*y+4*(x-y)*(x-y);
        if(candidate<score){score=candidate;best=modes[i];best.scale=1;}
    }
    return best;
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

// Mobile UI density expresses the user's logical dp/point scale, not hardware
// PPI. Preserve that logical workspace while encoding at the host's 1x/2x scale.
// Desktop minimum logical dimensions intentionally do not apply to this policy.
static inline DPWorkspace dp_workspace_from_ui_pixels(double width, double height, double density) {
    DPWorkspace result = {0, 0, 0};
    if (!isfinite(width) || !isfinite(height) || !isfinite(density) ||
        width <= 0 || height <= 0 || density < 0.5 || density > 8) return result;
    const int scale = density > 1 ? 2 : 1;
    const double preferred = scale / density;
    const double minimum = fmax(640.0 / width, 360.0 / height);
    const double maximum = fmin(DP_WORKSPACE_MAX_WIDTH / width, DP_WORKSPACE_MAX_HEIGHT / height);
    const double factor = fmin(fmax(preferred, minimum), maximum);
    result.width = (int)fmin(DP_WORKSPACE_MAX_WIDTH, ceil(width * factor / 4) * 4);
    result.height = (int)fmin(DP_WORKSPACE_MAX_HEIGHT, ceil(height * factor / 4) * 4);
    result.scale = scale;
    const DPWorkspace empty = {0, 0, 0};
    return dp_workspace_valid(result) ? result : empty;
}
// Apply the user's final workspace multiplier without changing host pixel scale.
// Clamp both axes by one factor so protocol bounds retain the aspect ratio.
static inline DPWorkspace dp_workspace_adjust(DPWorkspace base, double factor) {
    const DPWorkspace empty = {0, 0, 0};
    if (!dp_workspace_valid(base)) return empty;
    int allowed = 0;
    for (unsigned i=0; i<DP_CATALOG_TUNING_COUNT; ++i)
        if (fabs(factor-dp_catalog_tuning_values[i]) < 0.000001) allowed = 1;
    if (!allowed) factor = 1.0;
    factor = fmin(fmax(factor, fmax(640.0/base.width,360.0/base.height)),
                  fmin((double)DP_WORKSPACE_MAX_WIDTH/base.width,(double)DP_WORKSPACE_MAX_HEIGHT/base.height));
    const DPWorkspace result = {(int)(ceil(base.width*factor/4)*4),
                         (int)(ceil(base.height*factor/4)*4),base.scale};
    return result;
}
// Conservative macOS desktop floor, verified in both orientations. WindowServer
// can enumerate smaller HiDPI modes but reject selecting them. Apply after user
// tuning, retaining backing scale and aspect ratio; other hosts keep their policy.
static inline DPWorkspace dp_workspace_for_macos(DPWorkspace base) {
    const DPWorkspace empty = {0, 0, 0};
    if (!dp_workspace_valid(base)) return empty;
    const int portrait = base.height > base.width;
    const double minimumWidth = (portrait ? 600.0 : 800.0) * base.scale;
    const double minimumHeight = (portrait ? 800.0 : 600.0) * base.scale;
    const double factor = fmax(1.0, fmax(minimumWidth/base.width, minimumHeight/base.height));
    if (base.width*factor > DP_WORKSPACE_MAX_WIDTH || base.height*factor > DP_WORKSPACE_MAX_HEIGHT)
        return empty;
    const DPWorkspace result = {(int)(ceil(base.width*factor/4)*4),
                               (int)(ceil(base.height*factor/4)*4),base.scale};
    return result;
}
#endif
