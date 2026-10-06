#!/usr/bin/env python3
"""Reference parser for one-time pairing invitation URIs.

Consumers own their production parsers. This executable specification checks
that every shared fixture is accepted or rejected for the reason it names, so a
fixture cannot silently pass on an unrelated rule.
"""
import base64
import ipaddress
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "protocol/pairing-invite-cases.json").read_text(encoding="utf-8"))
PREFIX = "deskport://"
KEYS = ("v", "entry", "id", "fp", "token", "exp")
URI_LIMIT = 2048
EXPIRY_SKEW = 330


class Invalid(Exception):
    pass


def decode(raw):
    if "+" in raw or re.search(r"%(?![0-9A-Fa-f]{2})", raw):
        raise Invalid("escape")
    data = bytearray()
    index = 0
    while index < len(raw):
        if raw[index] == "%":
            data.append(int(raw[index + 1:index + 3], 16))
            index += 3
        else:
            if not "!" <= raw[index] <= "~":
                raise Invalid("character")
            data.append(ord(raw[index]))
            index += 1
    try:
        value = data.decode("utf-8")
    except UnicodeDecodeError:
        raise Invalid("escape")
    if not value or not re.fullmatch(r"[!-~]+", value):
        raise Invalid("character")
    return value


def entry_valid(entry):
    match = re.fullmatch(r"(\[[^\]]+\]|[^:\[\]]+):([1-9][0-9]{0,4})", entry)
    if not match or int(match.group(2)) > 65535:
        return False
    host = match.group(1)
    if host.startswith("["):
        literal = host[1:-1]
        if "%" in literal:
            return False
        try:
            ipaddress.IPv6Address(literal)
        except ValueError:
            return False
        return True
    if len(host) > 253 or not re.fullmatch(r"[A-Za-z0-9.-]+", host):
        return False
    if re.fullmatch(r"[0-9.]+", host):
        parts = host.split(".")
        return len(parts) == 4 and all(
            part and len(part) <= 3 and (part == "0" or not part.startswith("0")) and int(part) <= 255
            for part in parts)
    labels = host[:-1].split(".") if host.endswith(".") else host.split(".")
    return all(label and len(label) <= 63 and not label.startswith("-") and not label.endswith("-")
               for label in labels)


def parse(uri, now):
    if len(uri.encode("utf-8")) > URI_LIMIT:
        raise Invalid("length")
    if not uri.startswith(PREFIX):
        raise Invalid("scheme")
    rest = uri[len(PREFIX):]
    if "#" in rest:
        raise Invalid("fragment")
    authority, separator, query = rest.partition("?")
    if "@" in authority:
        raise Invalid("userinfo")
    if "/" in authority:
        raise Invalid("path")
    if authority != "bind":
        raise Invalid("authority")
    if not separator or not query:
        raise Invalid("field")
    fields = {}
    for part in query.split("&"):
        key, equals, raw = part.partition("=")
        if not equals or "=" in raw or key not in KEYS or key in fields:
            raise Invalid("field")
        fields[key] = decode(raw)
    if len(fields) != len(KEYS):
        raise Invalid("field")
    if fields["v"] != "1":
        raise Invalid("version")
    identifier = fields["id"]
    if (not re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", identifier) or
            set(identifier) <= {"0", "-"}):
        raise Invalid("id")
    if not re.fullmatch(r"[0-9a-f]{64}", fields["fp"]):
        raise Invalid("fp")
    token = fields["token"]
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        raise Invalid("token")
    secret = base64.urlsafe_b64decode(token + "=")
    if len(secret) != 32 or base64.urlsafe_b64encode(secret).decode().rstrip("=") != token:
        raise Invalid("token")
    if not re.fullmatch(r"[1-9][0-9]*", fields["exp"]):
        raise Invalid("exp")
    expires = int(fields["exp"])
    if not now < expires <= now + EXPIRY_SKEW:
        raise Invalid("expiry-window")
    if not entry_valid(fields["entry"]):
        raise Invalid("entry")
    return {"entry": fields["entry"], "hostId": identifier, "fingerprint": fields["fp"],
            "token": token, "expiresAt": expires}


def main():
    now = CASES["now"]
    names = set()
    for case in CASES["valid"]:
        assert case["name"] not in names, case["name"]
        names.add(case["name"])
        result = parse(case["uri"], now)
        for key, value in result.items():
            assert case[key] == value, (case["name"], key, value)
    for case in CASES["invalid"]:
        assert case["name"] not in names, case["name"]
        names.add(case["name"])
        try:
            parse(case["uri"], now)
        except Invalid as error:
            assert str(error) == case["reason"], (case["name"], str(error), case["reason"])
        else:
            raise AssertionError(f"{case['name']} was accepted")
    print(f"PASS: {len(CASES['valid'])} valid and {len(CASES['invalid'])} invalid pairing invitation fixtures")


if __name__ == "__main__":
    main()
