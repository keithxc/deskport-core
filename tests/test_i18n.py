#!/usr/bin/env python3
"""Check the public UI-only boundary, locale registry and formatting safety."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('core_ui_catalog', root/'i18n/catalog.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
languages = module.languages()
codes = [language['code'] for language in languages]
assert len(codes) == len(set(codes))
assert {'en','zh-Hans','zh-Hant','ja','fr','de','ar','ko','pt','es','bo'} == set(codes)
assert next(language for language in languages if language['code'] == 'ar')['direction'] == 'rtl'
rows = module.catalog()
records = module.records()
for platform in ('apple', 'android'):
    for source, row in module.catalog(platform).items():
        for code in codes:
            assert row.get(code), (platform, source, code)
            assert module.placeholders(source) == module.placeholders(row[code]), (platform, source, code)
for source, row in records.items():
    assert row['_platforms']['desktop'] or row['_platforms']['apple'] or row['_platforms']['android'] or row.get('_manual'), source
    for code, text in row.items():
        if code.startswith('_') or not text:
            continue
        # Qt numbered substitutions may reorder; native printf is checked in
        # order by the consumer before generating Apple/Android payloads.
        if code in codes:
            assert sorted(module.placeholders(source)) == sorted(module.placeholders(text)), (source, code)
    for context, translations in row.get('_qt', {}).items():
        for code, text in translations.items():
            if code in codes and text:
                assert sorted(module.placeholders(source)) == sorted(module.placeholders(text)), (source, context, code)
metadata = module.qt_catalogs()
for description in metadata.values():
    for context in description['contexts']:
        for message in context['messages']:
            assert message['source'] in records, message['source']
# These are wire/storage identifiers, not localizable UI text. Exact English
# UI labels such as "Connect" are separate from lowercase protocol messages.
for identifier in ('hello','displayPolicy','videoRate','video-rate','video-pause',
                   'sessionTakeover','pairing-invite','saver','requestedBitrate',
                   'desktopTuning','main-mirror','main-only','extended'):
    assert identifier not in rows, identifier
assert module.placeholders('%1 %@ %.1f %d %% %2') == ['%1','%@','%.1f','%d','%%','%2']
print(f'PASS: {len(rows)} UI-only entries; {len(codes)} locales, direction and placeholder safety')
subprocess.run([sys.executable, str(root/'i18n/generate_manual.py'), '--check'], check=True)
