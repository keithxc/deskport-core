#!/usr/bin/env python3
"""Generate the offline manual from the same English-keyed UI table."""
import argparse
import json
from pathlib import Path
from catalog import ROOT, records, languages

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
table = records()
manual = json.loads((ROOT/'manual.json').read_text())
codes = [language['code'] for language in languages()]
manual['languages'] = codes
for chapter in manual['chapters']:
    for container, field in [(chapter, 'title'), *[(step, 'text') for step in chapter['steps']]]:
        source = container[field]
        row = table[source]
        container[field] = {code: row[code] for code in codes if row.get(code)}
target = ROOT.parent/'manual/manual.json'
expected = json.dumps(manual, ensure_ascii=False, indent=2)+'\n'
if args.check:
    assert target.read_text() == expected, 'Regenerate manual with i18n/generate_manual.py'
else:
    target.write_text(expected)
print('PASS: offline manual matches the unified UI table')
