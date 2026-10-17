#!/usr/bin/env python3
"""Load UI resources only. Never apply this catalog to protocol/runtime data."""
# SPDX-License-Identifier: GPL-3.0-or-later
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def languages():
    return json.loads((ROOT / 'languages.json').read_text(encoding='utf-8'))


def placeholders(text):
    return re.findall(r'%(?:\d+\$)?(?:\.\d+)?(?:hh|ll|[hljztL])?[diuoxXfFeEgGaAcsp@]|%[1-9]\d*|%%', text)


def records():
    data = json.loads((ROOT / 'strings.json').read_text(encoding='utf-8'))
    for source, row in data.items():
        assert row['en'] == source, source
        assert set(row['_platforms']) == {'desktop', 'apple', 'android'}, source
        assert set(row.get('_web', [])) <= {'Browser'}, source
    return data


def catalog(platform=None):
    return {source: {code: text for code, text in row.items() if not code.startswith('_')}
            for source, row in records().items()
            if platform is None or row['_platforms'][platform]}


def qt_catalogs():
    data = json.loads((ROOT / 'qt.json').read_text(encoding='utf-8'))
    for description in data['catalogs'].values():
        for context in description['contexts']:
            context['messages'] = [data['messages'][key] for key in context['messages']]
    return data['catalogs']


if __name__ == '__main__':
    print(f'PASS: {len(catalog())} shared UI strings × {len(languages())} languages')
