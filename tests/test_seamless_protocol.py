#!/usr/bin/env python3
"""Compile the shared Seamless header and execute its stateful protocol vectors."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "protocol/seamless-cases.json").read_text(encoding="utf-8"))
LIMITS = CASES["limits"]
MESSAGES = CASES["messages"]
ERRORS = CASES["errors"]


def is_integer(value):
    return type(value) is int


def bounded_string(value, limit, optional=False):
    if optional and value is None:
        return True
    return isinstance(value, str) and len(value.encode("utf-8")) <= limit


def identifier_valid(value):
    return is_integer(value) and LIMITS["windowIdMin"] <= value <= LIMITS["windowIdMax"]


def sequence_valid(value):
    return is_integer(value) and LIMITS["sequenceMin"] <= value <= LIMITS["sequenceMax"]


def size_valid(width, height):
    return (is_integer(width) and is_integer(height) and
            LIMITS["windowMinWidth"] <= width <= LIMITS["windowMaxWidth"] and
            LIMITS["windowMinHeight"] <= height <= LIMITS["windowMaxHeight"])


def damage_valid(message, window_size):
    values = [message.get(name) for name in ("x", "y", "damageWidth", "damageHeight")]
    if not all(is_integer(value) for value in values):
        return False
    x, y, width, height = values
    window_width, window_height = window_size
    return (x >= 0 and y >= 0 and width > 0 and height > 0 and
            x <= window_width and y <= window_height and
            width <= window_width - x and height <= window_height - y)


def preflight_error(negotiation):
    mode = negotiation.get("sessionMode")
    if mode != CASES["capability"]["seamlessMode"]:
        return ERRORS["wrongSessionMode"] if mode == CASES["capability"]["desktopMode"] else ERRORS["invalidMessage"]
    if negotiation.get("advertisedVersion") != CASES["version"]:
        return ERRORS["modeNotAdvertised"]
    if negotiation.get("requestedVersion") != CASES["version"]:
        return ERRORS["unsupportedVersion"]
    return None


class ContractState:
    def __init__(self, negotiation):
        self.negotiation = negotiation
        self.active = {}
        self.retired = set()
        self.pending_resize = {}

    def _known(self, message):
        identifier = message.get("id")
        if not identifier_valid(identifier):
            return None, ERRORS["invalidMessage"]
        if identifier not in self.active:
            return None, ERRORS["unknownWindowId"]
        return identifier, None

    def control(self, step):
        wire_bytes = step.get("wireBytes")
        if not is_integer(wire_bytes) or wire_bytes <= 0 or wire_bytes > LIMITS["controlFrameBytes"]:
            return False, ERRORS["controlTooLarge"]
        message = step.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("type"), str):
            return False, ERRORS["invalidMessage"]
        kind = message["type"]
        seamless_types = set(MESSAGES.values()) - {MESSAGES["negotiate"], MESSAGES["result"]}
        if kind not in seamless_types:
            return False, ERRORS["invalidMessage"]
        negotiation_error = preflight_error(self.negotiation)
        if negotiation_error:
            return False, negotiation_error
        if not self.negotiation.get("sessionLease"):
            return False, ERRORS["wrongSessionMode"]

        if kind == MESSAGES["protocolError"]:
            if not isinstance(message.get("code"), str) or not message["code"]:
                return False, ERRORS["invalidMessage"]
            if "id" in message and not identifier_valid(message["id"]):
                return False, ERRORS["invalidMessage"]
            if "seq" in message and not sequence_valid(message["seq"]):
                return False, ERRORS["invalidMessage"]
            return True, None

        if kind == MESSAGES["windowCreate"]:
            identifier = message.get("id")
            if not identifier_valid(identifier):
                return False, ERRORS["invalidMessage"]
            if identifier in self.active or identifier in self.retired:
                return False, ERRORS["duplicateWindowId"]
            if len(self.active) >= LIMITS["maxActiveWindows"]:
                return False, ERRORS["tooManyWindows"]
            if not size_valid(message.get("width"), message.get("height")):
                return False, ERRORS["invalidWindowSize"]
            if (not bounded_string(message.get("title"), LIMITS["titleBytes"], optional=True) or
                    not bounded_string(message.get("appId"), LIMITS["appIdBytes"], optional=True)):
                return False, ERRORS["invalidMessage"]
            self.active[identifier] = (message["width"], message["height"])
            return True, None

        identifier, error = self._known(message)
        if error:
            return False, error

        if kind == MESSAGES["windowDestroy"]:
            reason = message.get("reason")
            if not bounded_string(reason, LIMITS["titleBytes"], optional=True):
                return False, ERRORS["invalidMessage"]
            del self.active[identifier]
            self.retired.add(identifier)
            self.pending_resize.pop(identifier, None)
            return True, None
        if kind == MESSAGES["windowTitle"]:
            if not bounded_string(message.get("title"), LIMITS["titleBytes"]):
                return False, ERRORS["invalidMessage"]
            return True, None
        if kind == MESSAGES["windowResizeRequest"]:
            sequence = message.get("seq")
            if not sequence_valid(sequence):
                return False, ERRORS["invalidMessage"]
            if identifier in self.pending_resize:
                return False, ERRORS["invalidMessage"]
            if not size_valid(message.get("width"), message.get("height")):
                return False, ERRORS["invalidWindowSize"]
            self.pending_resize[identifier] = (sequence, message["width"], message["height"])
            return True, None
        if kind == MESSAGES["windowResizeResult"]:
            sequence = message.get("seq")
            pending = self.pending_resize.get(identifier)
            if not sequence_valid(sequence) or not pending or pending[0] != sequence:
                return False, ERRORS["invalidMessage"]
            if "error" in message:
                if not bounded_string(message.get("error"), LIMITS["titleBytes"]) or not message["error"]:
                    return False, ERRORS["invalidMessage"]
            else:
                if not size_valid(message.get("width"), message.get("height")):
                    return False, ERRORS["invalidWindowSize"]
                self.active[identifier] = (message["width"], message["height"])
            del self.pending_resize[identifier]
            return True, None
        if kind == MESSAGES["windowFocus"]:
            return ((True, None) if type(message.get("focused")) is bool
                    else (False, ERRORS["invalidMessage"]))
        if kind == MESSAGES["windowClose"]:
            return True, None
        if kind in (MESSAGES["windowCursor"], MESSAGES["inputPointer"], MESSAGES["inputKeyboard"]):
            # Version 1 reserves these names but their schema/capabilities are
            # deliberately deferred beyond the Milestone 1 preflight.
            return False, ERRORS["invalidMessage"]
        return False, ERRORS["invalidMessage"]

    def media(self, step):
        negotiation_error = preflight_error(self.negotiation)
        if negotiation_error:
            return False, negotiation_error
        if not self.negotiation.get("sessionLease"):
            return False, ERRORS["wrongSessionMode"]
        if not self.negotiation.get("mediaNegotiated"):
            return False, ERRORS["mediaNotNegotiated"]
        message = step.get("message")
        if not isinstance(message, dict):
            return False, ERRORS["invalidMessage"]
        if message.get("version") != CASES["version"]:
            return False, ERRORS["unsupportedVersion"]
        identifier = message.get("id")
        if not identifier_valid(identifier):
            return False, ERRORS["invalidMessage"]
        if identifier not in self.active:
            return False, ERRORS["unknownWindowId"]
        if not sequence_valid(message.get("seq")):
            return False, ERRORS["invalidMessage"]
        payload = message.get("payloadBytes")
        if not is_integer(payload) or payload <= 0 or payload > LIMITS["encodedFrameBytes"]:
            return False, ERRORS["frameTooLarge"]
        visible = (message.get("width"), message.get("height"))
        if not size_valid(*visible) or visible != self.active[identifier]:
            return False, ERRORS["invalidWindowSize"]
        if message.get("kind") == "frame":
            return True, None
        if message.get("kind") == "damage":
            return ((True, None) if damage_valid(message, visible)
                    else (False, ERRORS["invalidWindowSize"]))
        return False, ERRORS["invalidMessage"]


def compile_header_contract():
    macro_strings = {
        "DP_SEAMLESS_CAPABILITY": CASES["capability"]["field"],
        "DP_SEAMLESS_VERSION_FIELD": CASES["capability"]["versionField"],
        "DP_SESSION_MODE_FIELD": CASES["capability"]["sessionModeField"],
        "DP_SESSION_MODE_DESKTOP": CASES["capability"]["desktopMode"],
        "DP_SESSION_MODE_SEAMLESS": CASES["capability"]["seamlessMode"],
        "DP_MESSAGE_SEAMLESS_NEGOTIATE": MESSAGES["negotiate"],
        "DP_MESSAGE_SEAMLESS_RESULT": MESSAGES["result"],
        "DP_MESSAGE_SEAMLESS_WINDOW_CREATE": MESSAGES["windowCreate"],
        "DP_MESSAGE_SEAMLESS_WINDOW_DESTROY": MESSAGES["windowDestroy"],
        "DP_MESSAGE_SEAMLESS_WINDOW_TITLE": MESSAGES["windowTitle"],
        "DP_MESSAGE_SEAMLESS_WINDOW_RESIZE_REQUEST": MESSAGES["windowResizeRequest"],
        "DP_MESSAGE_SEAMLESS_WINDOW_RESIZE_RESULT": MESSAGES["windowResizeResult"],
        "DP_MESSAGE_SEAMLESS_WINDOW_CLOSE": MESSAGES["windowClose"],
        "DP_MESSAGE_SEAMLESS_WINDOW_CURSOR": MESSAGES["windowCursor"],
        "DP_MESSAGE_SEAMLESS_WINDOW_FOCUS": MESSAGES["windowFocus"],
        "DP_MESSAGE_SEAMLESS_INPUT_POINTER": MESSAGES["inputPointer"],
        "DP_MESSAGE_SEAMLESS_INPUT_KEYBOARD": MESSAGES["inputKeyboard"],
        "DP_MESSAGE_SEAMLESS_PROTOCOL_ERROR": MESSAGES["protocolError"],
        "DP_SEAMLESS_ERROR_UNSUPPORTED_VERSION": ERRORS["unsupportedVersion"],
        "DP_SEAMLESS_ERROR_MODE_NOT_ADVERTISED": ERRORS["modeNotAdvertised"],
        "DP_SEAMLESS_ERROR_WRONG_SESSION_MODE": ERRORS["wrongSessionMode"],
        "DP_SEAMLESS_ERROR_INVALID_MESSAGE": ERRORS["invalidMessage"],
        "DP_SEAMLESS_ERROR_CONTROL_TOO_LARGE": ERRORS["controlTooLarge"],
        "DP_SEAMLESS_ERROR_TOO_MANY_WINDOWS": ERRORS["tooManyWindows"],
        "DP_SEAMLESS_ERROR_DUPLICATE_WINDOW_ID": ERRORS["duplicateWindowId"],
        "DP_SEAMLESS_ERROR_UNKNOWN_WINDOW_ID": ERRORS["unknownWindowId"],
        "DP_SEAMLESS_ERROR_INVALID_WINDOW_SIZE": ERRORS["invalidWindowSize"],
        "DP_SEAMLESS_ERROR_MEDIA_NOT_NEGOTIATED": ERRORS["mediaNotNegotiated"],
        "DP_SEAMLESS_ERROR_FRAME_TOO_LARGE": ERRORS["frameTooLarge"],
    }
    macro_numbers = {
        "DP_SEAMLESS_PROTOCOL_VERSION": CASES["version"],
        "DP_SEAMLESS_WINDOW_ID_MIN": LIMITS["windowIdMin"],
        "DP_SEAMLESS_WINDOW_ID_MAX": LIMITS["windowIdMax"],
        "DP_SEAMLESS_SEQUENCE_MIN": LIMITS["sequenceMin"],
        "DP_SEAMLESS_SEQUENCE_MAX": LIMITS["sequenceMax"],
        "DP_SEAMLESS_MAX_ACTIVE_WINDOWS": LIMITS["maxActiveWindows"],
        "DP_SEAMLESS_WINDOW_MIN_WIDTH": LIMITS["windowMinWidth"],
        "DP_SEAMLESS_WINDOW_MIN_HEIGHT": LIMITS["windowMinHeight"],
        "DP_SEAMLESS_WINDOW_MAX_WIDTH": LIMITS["windowMaxWidth"],
        "DP_SEAMLESS_WINDOW_MAX_HEIGHT": LIMITS["windowMaxHeight"],
        "DP_SEAMLESS_WINDOW_TITLE_LIMIT": LIMITS["titleBytes"],
        "DP_SEAMLESS_APP_ID_LIMIT": LIMITS["appIdBytes"],
        "DP_SEAMLESS_CONTROL_FRAME_LIMIT": LIMITS["controlFrameBytes"],
        "DP_SEAMLESS_ENCODED_FRAME_LIMIT": LIMITS["encodedFrameBytes"],
        "DP_SEAMLESS_MEDIA_FRAME": CASES["mediaKinds"]["frame"],
        "DP_SEAMLESS_MEDIA_DAMAGE": CASES["mediaKinds"]["damage"],
    }
    lines = [
        "#include <assert.h>",
        "#include <stdint.h>",
        "#include <string.h>",
        f'#include "{(ROOT / "include/deskport/protocol.h").resolve()}"',
        "int main(void) {",
    ]
    lines.extend(f"assert(strcmp({macro}, {json.dumps(value)}) == 0);"
                 for macro, value in macro_strings.items())
    lines.extend(f"assert((uint64_t)({macro}) == UINT64_C({value}));"
                 for macro, value in macro_numbers.items())
    lines.extend([
        "assert(dp_session_mode_is_desktop(0));",
        "assert(dp_session_mode_is_desktop(DP_SESSION_MODE_DESKTOP));",
        "assert(!dp_session_mode_is_desktop(DP_SESSION_MODE_SEAMLESS));",
        "assert(dp_seamless_preflight_valid(DP_SESSION_MODE_SEAMLESS, 1, 1));",
        "assert(!dp_seamless_preflight_valid(DP_SESSION_MODE_DESKTOP, 1, 1));",
        "assert(!dp_seamless_preflight_valid(DP_SESSION_MODE_SEAMLESS, 0, 1));",
        "assert(!dp_seamless_preflight_valid(DP_SESSION_MODE_SEAMLESS, 1, 2));",
        "assert(dp_seamless_window_id_valid(DP_SEAMLESS_WINDOW_ID_MIN));",
        "assert(dp_seamless_window_id_valid(DP_SEAMLESS_WINDOW_ID_MAX));",
        "assert(!dp_seamless_window_id_valid(0));",
        "assert(!dp_seamless_window_id_valid(UINT64_C(2147483648)));",
        "assert(dp_seamless_sequence_valid(DP_SEAMLESS_SEQUENCE_MIN));",
        "assert(!dp_seamless_sequence_valid(0));",
        "assert(dp_seamless_window_size_valid(16, 16));",
        "assert(dp_seamless_window_size_valid(7680, 4320));",
        "assert(!dp_seamless_window_size_valid(15, 600));",
        "assert(!dp_seamless_window_size_valid(800, 4321));",
        "assert(dp_seamless_damage_rect_valid(790, 590, 10, 10, 800, 600));",
        "assert(!dp_seamless_damage_rect_valid(790, 590, 11, 10, 800, 600));",
        "assert(!dp_seamless_damage_rect_valid(-1, 0, 1, 1, 800, 600));",
        "assert(dp_seamless_control_frame_size_valid(32768));",
        "assert(!dp_seamless_control_frame_size_valid(0));",
        "assert(!dp_seamless_control_frame_size_valid(32769));",
        "assert(dp_seamless_encoded_frame_size_valid(UINT64_C(33554432)));",
        "assert(!dp_seamless_encoded_frame_size_valid(0));",
        "assert(!dp_seamless_encoded_frame_size_valid(UINT64_C(33554433)));",
        "return 0;",
        "}",
    ])
    with tempfile.TemporaryDirectory(prefix="deskport-seamless-") as directory:
        work = Path(directory)
        for language, compiler, standard in [
            ("c", os.environ.get("CC", "/usr/bin/clang" if sys.platform == "darwin" else "cc"), "c11"),
            ("cpp", os.environ.get("CXX", "/usr/bin/clang++" if sys.platform == "darwin" else "c++"), "c++17"),
        ]:
            source = work / f"contract.{language}"
            binary = work / f"contract-{language}"
            source.write_text("\n".join(lines) + "\n", encoding="utf-8")
            subprocess.run([compiler, f"-std={standard}", "-Wall", "-Wextra", "-Werror", "-pedantic",
                            "-fsanitize=undefined,address", str(source), "-o", str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


def validate_preflight_vectors():
    preflight = CASES["preflight"]
    request = preflight["request"]
    assert request == {
        "type": MESSAGES["negotiate"],
        CASES["capability"]["sessionModeField"]: CASES["capability"]["seamlessMode"],
        CASES["capability"]["versionField"]: CASES["version"],
    }
    accepted = preflight["acceptedResult"]
    assert accepted["type"] == MESSAGES["result"] and accepted["accepted"] is True
    assert "code" not in accepted and "error" not in accepted
    rejected = preflight["unsupportedResult"]
    assert rejected["type"] == MESSAGES["result"] and rejected["accepted"] is False
    assert rejected["code"] == ERRORS["unsupportedVersion"]
    assert "error" not in rejected or isinstance(rejected["error"], str)


def run_vectors():
    required = {
        "preflight-success-does-not-admit-session",
        "valid-window-lifecycle",
        "wrong-version-fails-without-fallback",
        "duplicate-retired-and-unknown-ids",
        "invalid-identifiers-and-dimensions",
        "control-and-media-size-limits",
        "media-requires-separate-negotiation",
        "desktop-and-seamless-isolation",
    }
    scenarios = CASES["scenarios"]
    names = [scenario["name"] for scenario in scenarios]
    assert len(names) == len(set(names)), "duplicate scenario name"
    assert required.issubset(names), required - set(names)
    checked = 0
    for scenario in scenarios:
        state = ContractState(scenario["negotiation"])
        for step in scenario["steps"]:
            before = copy.deepcopy((state.active, state.retired, state.pending_resize))
            if step["plane"] == "control":
                accepted, error = state.control(step)
            elif step["plane"] == "media":
                accepted, error = state.media(step)
            else:
                raise AssertionError((scenario["name"], step["plane"]))
            assert accepted is step["accepted"], (scenario["name"], step, accepted, error)
            assert error == step.get("error"), (scenario["name"], step, error)
            if not accepted:
                after = (state.active, state.retired, state.pending_resize)
                assert after == before, (scenario["name"], "rejection mutated state")
            checked += 1
    return checked


def main():
    assert CASES["version"] == 1
    validate_preflight_vectors()
    compile_header_contract()
    checked = run_vectors()
    print(f"PASS: Seamless protocol header in C/C++ and {checked} stateful vector steps")


if __name__ == "__main__":
    main()
