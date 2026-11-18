// SPDX-License-Identifier: MIT
/* Deliberately synthetic wire values, not any consumer's protocol definitions.
 * Compile and run this same fixture as both C11 and C++11. */
enum FakeWireButton {
    DP_BUTTON_PRIMARY = 101, DP_BUTTON_SECONDARY = 102,
    DP_BUTTON_MIDDLE = 103, DP_BUTTON_BACK = 104, DP_BUTTON_FORWARD = 105
};
enum FakeWireInput {
    DP_INPUT_KEY_DOWN = 201, DP_INPUT_KEY_UP = 202,
    DP_INPUT_POINTER_ABSOLUTE = 203, DP_INPUT_POINTER_RELATIVE = 204,
    DP_INPUT_BUTTON_DOWN = 205, DP_INPUT_BUTTON_UP = 206, DP_INPUT_SCROLL = 207
};

/* A consumer's common native entry header must set this before any core include. */
#define DP_DISABLE_LOCAL_INPUT_ALIASES
#include "deskport/catalog.h"
#include "deskport/contracts.h"
#include "deskport/input.h"
#include "deskport/session.h"
#include "deskport/stream_budget.h"
#include "deskport/tuning.h"
#include "deskport/view_size.h"
#include "deskport/workspace.h"
#include <assert.h>

#if defined(DP_BUTTON_PRIMARY) || defined(DP_BUTTON_SECONDARY) || \
    defined(DP_BUTTON_MIDDLE) || defined(DP_BUTTON_BACK) || defined(DP_BUTTON_FORWARD) || \
    defined(DP_INPUT_KEY_DOWN) || defined(DP_INPUT_KEY_UP) || \
    defined(DP_INPUT_POINTER_ABSOLUTE) || defined(DP_INPUT_POINTER_RELATIVE) || \
    defined(DP_INPUT_BUTTON_DOWN) || defined(DP_INPUT_BUTTON_UP) || defined(DP_INPUT_SCROLL)
#error Local compatibility aliases must not rewrite wire enum identifiers
#endif

int main(void) {
    int value;
    assert(DP_BUTTON_PRIMARY == 101 && DP_BUTTON_SECONDARY == 102);
    assert(DP_BUTTON_MIDDLE == 103 && DP_BUTTON_BACK == 104 && DP_BUTTON_FORWARD == 105);
    assert(DP_INPUT_KEY_DOWN == 201 && DP_INPUT_KEY_UP == 202);
    assert(DP_INPUT_POINTER_ABSOLUTE == 203 && DP_INPUT_POINTER_RELATIVE == 204);
    assert(DP_INPUT_BUTTON_DOWN == 205 && DP_INPUT_BUTTON_UP == 206 && DP_INPUT_SCROLL == 207);
    assert(DP_LOCAL_BUTTON_PRIMARY == 1 && DP_LOCAL_BUTTON_SECONDARY == 2);
    assert(DP_LOCAL_BUTTON_MIDDLE == 3 && DP_LOCAL_BUTTON_BACK == 4 && DP_LOCAL_BUTTON_FORWARD == 5);
    assert(DP_LOCAL_INPUT_KEY_DOWN == 1 && DP_LOCAL_INPUT_KEY_UP == 2);
    assert(DP_LOCAL_INPUT_POINTER_ABSOLUTE == 3 && DP_LOCAL_INPUT_POINTER_RELATIVE == 4);
    assert(DP_LOCAL_INPUT_BUTTON_DOWN == 5 && DP_LOCAL_INPUT_BUTTON_UP == 6 && DP_LOCAL_INPUT_SCROLL == 7);
    for (value = -1; value <= 208; ++value) {
        assert(dp_contract_button_valid(value) == (value >= 1 && value <= 5));
        assert(dp_contract_input_kind_valid(value) == (value >= 1 && value <= 7));
    }
    /* No alias opt-out may remove or alter these independent vocabularies. */
    assert(DP_HID_PAGE_KEYBOARD == 7 && DP_HID_PAGE_BUTTON == 9);
    assert(DP_HID_KEY_A == 4 && DP_HID_KEY_NON_US_BACKSLASH == 0x64);
    assert(DP_HID_KEY_INTERNATIONAL_3 == 0x89);
    assert(DP_VK_LSHIFT == 0xa0 && DP_VK_RSHIFT == 0xa1 && DP_VK_OEM_102 == 0xe2);
    assert(DP_MOD_LEFT_CONTROL == 1 && DP_MOD_RIGHT_CONTROL == 16);
    assert(dp_input_modifier_for_hid(DP_HID_KEY_LEFT_CONTROL) == DP_MOD_LEFT_CONTROL);
    assert(dp_input_modifier_for_hid(DP_HID_KEY_RIGHT_CONTROL) == DP_MOD_RIGHT_CONTROL);
    assert(dp_contract_hid_key_valid(DP_HID_KEY_A));
    assert(dp_contract_virtual_key_valid(DP_VK_OEM_102));
    assert(!dp_contract_virtual_key_valid(256));
    return 0;
}
