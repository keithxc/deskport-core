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
/* Drawable proposals use the desktop 1920x1080 preferred pixel floor.
 * An extreme aspect may produce a proposal outside the wire minimum: callers
 * must use dp_workspace_valid before sending it. No encoded pixels are rescaled
 * by dp_workspace_from_encoded. */
static inline DPWorkspace dp_workspace_drawable_proposal(double w, double h,
                                                          double multiplier, int scale) {
    DPWorkspace result = {0, 0, 0};
    if (!isfinite(w) || !isfinite(h) || w <= 0 || h <= 0 ||
        !isfinite(multiplier) || multiplier < 1 || multiplier > 8 || (scale != 1 && scale != 2)) return result;
    double longest = fmax(w, h);
    double x = w / longest, y = h / longest;
    /* Pick the limiting axis without dividing by a possibly subnormal ratio.
     * Saturate the preferred and lower edges before multiplication/division. */
    double upper = x * 4320 > y * 7680 ? 7680 / x : 4320 / y;
    double lower_w = x * upper < 1920 ? upper : 1920 / x;
    double lower_h = y * upper < 1080 ? upper : 1080 / y;
    int preferred_fits = longest <= upper / multiplier;
    double preferred = preferred_fits ? longest * multiplier : upper;
    double edge = fmax(fmax(lower_w, lower_h), preferred);
    double exact_w = preferred_fits && edge == preferred ? w * multiplier : x * edge;
    double exact_h = preferred_fits && edge == preferred ? h * multiplier : y * edge;
    result.width = (int)fmin(7680, fmax(4, 4 * ceil(exact_w / 4)));
    result.height = (int)fmin(4320, fmax(4, 4 * ceil(exact_h / 4)));
    result.scale = scale;
    return result;
}

/* Drawable pixels; density above two does not reduce the supplied pixels. */
static inline DPWorkspace dp_workspace_from_drawable_pixels(double width, double height,
                                                            double density) {
    DPWorkspace invalid = {0, 0, 0};
    if (!isfinite(width) || !isfinite(height) || !isfinite(density) ||
        width <= 0 || height <= 0 || density < 0.5 || density > 8) return invalid;
    int scale = density > 1 ? 2 : 1;
    return dp_workspace_drawable_proposal(width, height, scale / fmin(density, 2), scale);
}

/* Logical drawable rectangle, distinct from the existing logical UI viewport.
 * Reject transient rectangles and proposals that cannot satisfy the wire box. */
static inline DPWorkspace dp_workspace_from_drawable_viewport(double width, double height,
                                                              double density) {
    DPWorkspace invalid = {0, 0, 0};
    if (!isfinite(width) || !isfinite(height) || !isfinite(density) ||
        width < 128 || height < 128 || density < 0.5 || density > 8) return invalid;
    int scale = density > 1 ? 2 : 1;
    DPWorkspace value = dp_workspace_drawable_proposal(width, height, fmax(scale, density), scale);
    return dp_workspace_from_encoded(value.width, value.height, value.scale);
}

/* Fit a valid encoded base with an independently supplied positive ratio. */
static inline DPWorkspace dp_workspace_fit_ratio(DPWorkspace base, DPTuningRatio ratio) {
    DPWorkspace invalid = {0, 0, 0};
    /* Restrict helper ratios to the bounded workspace domain before products. */
    if (!dp_workspace_valid(base) || ratio.numerator < 1 || ratio.numerator > 7680 ||
        ratio.denominator < 1 || ratio.denominator > 7680) return invalid;
    DPTuningRatio min_w = {640, base.width}, min_h = {360, base.height};
    DPTuningRatio max_w = {7680, base.width}, max_h = {4320, base.height};
    DPTuningRatio lower = dp_tuning_less(min_w, min_h) ? min_h : min_w;
    DPTuningRatio upper = dp_tuning_less(max_w, max_h) ? max_w : max_h;
    if (dp_tuning_less(ratio, lower)) ratio = lower;
    if (dp_tuning_less(upper, ratio)) ratio = upper;
    return dp_workspace_from_encoded(dp_tuning_aligned(base.width, ratio),
                                     dp_tuning_aligned(base.height, ratio), base.scale);
}

/* Protocol-only zoom: choose a catalog factor, fit the wire box, then ceil to
 * four pixels. Scale remains metadata. Unsupported factors preserve the base. */
static inline DPWorkspace dp_workspace_adjust(DPWorkspace base, double tuning) {
    DPWorkspace invalid = {0, 0, 0};
    if (!dp_workspace_valid(base)) return invalid;
    DPTuningRatio ratio = {1, 1};
    for (int i = 0; i < DP_CATALOG_TUNING_COUNT; ++i) {
        double delta = tuning - dp_catalog_tuning_values[i];
        if (delta > -0.000001 && delta < 0.000001) {
            ratio.numerator = 10;
            ratio.denominator = (int)(10 * dp_catalog_tuning_values[i] + 0.5);
            break;
        }
    }
    return dp_workspace_fit_ratio(base, ratio);
}

/* Apply the existing orientation-aware 800x600 logical host floor explicitly.
 * Compose after adjust when the protocol-adjusted, quantized aspect is required. */
static inline DPWorkspace dp_workspace_for_host(DPWorkspace base) {
    return dp_workspace_tuned(base, 1.0);
}

static inline DPWorkspace dp_workspace_for_macos(DPWorkspace base) {
    return dp_workspace_for_host(base);
}

static inline DPWorkspace dp_workspace_for_windows(DPWorkspace base) {
    return dp_workspace_for_host(base);
}

/* Saver keeps the logical desktop at scale one, subject to the wire minimum. */
static inline DPWorkspace dp_workspace_for_saver(DPWorkspace base) {
    DPWorkspace invalid = {0, 0, 0};
    if (!dp_workspace_valid(base)) return invalid;
    DPWorkspace single = {base.width, base.height, 1};
    DPTuningRatio ratio = {1, base.scale};
    return dp_workspace_fit_ratio(single, ratio);
}

/* No protocol ranking is specified. Original deterministic lexicographic rule:
 * orientation mismatch, normalized aspect error, squared pixel distance, order.
 * Aspect errors are rational; bounded dimensions make uint64 cross products safe.
 * Scale metadata does not affect dimension ranking; return the advertised scale. */
static inline DPWorkspace dp_workspace_select_mode(DPWorkspace request,
                                                   const DPWorkspace *modes, int count) {
    DPWorkspace invalid = {0, 0, 0};
    if (!dp_workspace_valid(request) || count < 0 || count > 96 ||
        (count > 0 && !modes)) return invalid;
    if (!count) return request;
    for (int i = 0; i < count; ++i) if (!dp_workspace_valid(modes[i])) return invalid;
    int best = 0;
    uint64_t best_error = 0, best_denominator = 1, best_distance = 0;
    int best_direction = 2;
    for (int i = 0; i < count; ++i) {
        DPWorkspace mode = modes[i];
        int direction = (mode.height > mode.width) != (request.height > request.width);
        int64_t cross = (int64_t)mode.width * request.height - (int64_t)request.width * mode.height;
        uint64_t error = (uint64_t)(cross < 0 ? -cross : cross);
        uint64_t denominator = (uint64_t)mode.height * request.height;
        int64_t dx = mode.width - request.width, dy = mode.height - request.height;
        uint64_t distance = (uint64_t)(dx * dx + dy * dy);
        uint64_t left = error * best_denominator, right = best_error * denominator;
        if (direction < best_direction || (direction == best_direction &&
            (left < right || (left == right && distance < best_distance)))) {
            best = i;
            best_direction = direction;
            best_error = error;
            best_denominator = denominator;
            best_distance = distance;
        }
    }
    return modes[best];
}
#endif
