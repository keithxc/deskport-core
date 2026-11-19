// SPDX-License-Identifier: MIT
#ifndef DESKPORT_PORTABLE_DESKTOP_WORKSPACE_H
#define DESKPORT_PORTABLE_DESKTOP_WORKSPACE_H

#include "workspace.h"

/* Desktop compatibility policy, independently implemented from the published
 * product formulas. Keep binary double arithmetic and its evaluation order:
 * rational reduction and aspect normalization can move a four-pixel boundary. */
static inline double dp_desktop_workspace_align(double pixels) {
    return ceil(pixels / 4.0) * 4.0;
}

static inline DPWorkspace dp_desktop_workspace_scaled(DPWorkspace base, double factor) {
    DPWorkspace result = {
        (int)dp_desktop_workspace_align(base.width * factor),
        (int)dp_desktop_workspace_align(base.height * factor),
        base.scale
    };
    return result;
}

/* Pixel proposals may be outside the wire minimum at extreme aspect ratios.
 * Cap each aligned axis before integer conversion, including infinite products. */
static inline DPWorkspace dp_desktop_workspace_from_pixels(double w, double h,
                                                           double density) {
    DPWorkspace invalid = {0, 0, 0};
    if (!isfinite(w) || !isfinite(h) || !isfinite(density) ||
        w <= 0 || h <= 0 || density < 0.5 || density > 8) return invalid;
    int scale = density > 1 ? 2 : 1;
    double preferred = fmax(fmax(1.0, scale / density),
                            fmax(960.0 * scale / w, 540.0 * scale / h));
    double factor = fmin(preferred, fmin(7680.0 / w, 4320.0 / h));
    DPWorkspace result = {
        (int)fmin(7680.0, dp_desktop_workspace_align(w * factor)),
        (int)fmin(4320.0, dp_desktop_workspace_align(h * factor)),
        scale
    };
    return result;
}

/* A near-catalog factor uses the supplied double, not the catalog value.
 * Do not clip the dimensions again after alignment. */
static inline DPWorkspace dp_desktop_workspace_adjust(DPWorkspace base, double tuning) {
    DPWorkspace invalid = {0, 0, 0};
    if (!dp_workspace_valid(base)) return invalid;
    double factor = 1.0;
    for (int i = 0; i < DP_CATALOG_TUNING_COUNT; ++i) {
        if (fabs(tuning - dp_catalog_tuning_values[i]) < 1e-6) {
            factor = 1.0 / tuning;
            break;
        }
    }
    double lower = fmax(640.0 / base.width, 360.0 / base.height);
    double upper = fmin(7680.0 / base.width, 4320.0 / base.height);
    factor = fmin(fmax(factor, lower), upper);
    return dp_desktop_workspace_scaled(base, factor);
}

/* Apply the orientation-aware logical floor while preserving backing scale.
 * Reject oversize products before four-pixel alignment. */
static inline DPWorkspace dp_desktop_workspace_for_host(DPWorkspace base) {
    DPWorkspace invalid = {0, 0, 0};
    if (!dp_workspace_valid(base)) return invalid;
    double min_w = (base.height > base.width ? 600.0 : 800.0) * base.scale;
    double min_h = (base.height > base.width ? 800.0 : 600.0) * base.scale;
    double factor = fmax(1.0, fmax(min_w / base.width, min_h / base.height));
    if (base.width * factor > 7680.0 || base.height * factor > 4320.0) return invalid;
    return dp_desktop_workspace_scaled(base, factor);
}

static inline DPWorkspace dp_desktop_workspace_for_saver(DPWorkspace base) {
    DPWorkspace invalid = {0, 0, 0};
    if (!dp_workspace_valid(base)) return invalid;
    if (base.scale == 1) return base;
    double factor = fmax(0.5, fmax(640.0 / base.width, 360.0 / base.height));
    base.scale = 1;
    return dp_desktop_workspace_scaled(base, factor);
}

/* Validate the entire table before ranking; strict improvement preserves ties.
 * An empty table preserves the request, including its scale metadata. */
static inline DPWorkspace dp_desktop_workspace_select_mode(DPWorkspace request,
                                                           const DPWorkspace *modes,
                                                           int count) {
    DPWorkspace invalid = {0, 0, 0};
    if (!dp_workspace_valid(request) || count < 0 || count > 96 ||
        (count > 0 && !modes)) return invalid;
    if (count == 0) return request;
    for (int i = 0; i < count; ++i) {
        if (!dp_workspace_valid(modes[i])) return invalid;
    }
    int best = 0;
    double best_score = HUGE_VAL;
    for (int i = 0; i < count; ++i) {
        double x = log((double)modes[i].width / request.width);
        double y = log((double)modes[i].height / request.height);
        double score = x * x + y * y + 4.0 * (x - y) * (x - y);
        if (score < best_score) {
            best = i;
            best_score = score;
        }
    }
    DPWorkspace result = {modes[best].width, modes[best].height, 1};
    return result;
}

#endif
