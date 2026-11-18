// SPDX-License-Identifier: MIT
#ifndef DESKPORT_PORTABLE_WORKSPACE_H
#define DESKPORT_PORTABLE_WORKSPACE_H

#include "contracts.h"
#include "view_size.h"
#include "tuning.h"

typedef struct { int width, height, scale; } DPWorkspace;

static inline int dp_workspace_valid(DPWorkspace value) {
    return dp_contract_workspace_valid(value.width, value.height, value.scale);
}

/* Field equality deliberately does not imply validity. */
static inline int dp_workspace_equal(DPWorkspace a, DPWorkspace b) {
    return a.width == b.width && a.height == b.height && a.scale == b.scale;
}

/* Drawable dimensions are already encoded pixels. Scale is metadata only. */
static inline DPWorkspace dp_workspace_from_encoded(int width, int height, int scale) {
    DPWorkspace value = {width, height, scale};
    DPWorkspace invalid = {0, 0, 0};
    return dp_workspace_valid(value) ? value : invalid;
}

static inline DPWorkspace dp_workspace_from_viewport(double width, double height, double density) {
    DPWorkspace value = {0, 0, 0};
    value.scale = dp_view_workspace(width, height, density, &value.width, &value.height);
    return dp_workspace_from_encoded(value.width, value.height, value.scale);
}

/* Existing tuning owns quantization, factor fallback and host floor policy. */
static inline DPWorkspace dp_workspace_tuned(DPWorkspace base, double tuning) {
    DPWorkspace value = {0, 0, 0};
    if (dp_tuned_desktop_size(base.width, base.height, base.scale, tuning,
                              &value.width, &value.height)) value.scale = base.scale;
    return dp_workspace_from_encoded(value.width, value.height, value.scale);
}

static inline DPWorkspace dp_workspace_for_viewport(double width, double height,
                                                    double density, double tuning) {
    return dp_workspace_tuned(dp_workspace_from_viewport(width, height, density), tuning);
}
#endif
