// SPDX-License-Identifier: MIT
#ifndef DESKPORT_PORTABLE_INPUT_H
#define DESKPORT_PORTABLE_INPUT_H

#include "contracts.h"

/* HID_KEY_* are usage IDs on HID_PAGE_KEYBOARD, not text or scan codes.
 * MOD_* bits retain left/right location in HID modifier-byte order.
 * LOCAL_BUTTON_* are local primary/secondary/etc. usages; LOCAL_INPUT_* are local event
 * kinds only. Neither defines serialization for a media input protocol.
 * VK_* is a deliberately small official WinVK vocabulary; the whitelist also
 * accepts digits, letters, numpad and F1..F24. Unsupported values fail closed.
 * No HID/WinVK conversion is implied: ISO/JIS layout routing belongs to adapters.
 */
static inline int dp_input_modifier_for_hid(int usage) {
    return usage >= DP_HID_KEY_LEFT_CONTROL && usage <= DP_HID_KEY_RIGHT_GUI ?
        1 << (usage - DP_HID_KEY_LEFT_CONTROL) : 0;
}
#endif
