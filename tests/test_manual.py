#!/usr/bin/env python3
"""Check the shared manual: structure, language fallback and bundled images."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
manual = json.loads((ROOT / 'manual/manual.json').read_text(encoding='utf-8'))

assert manual['version'] == 1, manual['version']
languages = manual['languages']
assert languages and languages[0] == 'en', languages
assert len(set(languages)) == len(languages), languages

seen = set()
for chapter in manual['chapters']:
    identifier = chapter['id']
    assert identifier and identifier not in seen, identifier
    seen.add(identifier)
    assert identifier.replace('-', '').isalnum(), identifier
    entries = [chapter['title']] + [step['text'] for step in chapter['steps']]
    assert chapter['steps'], identifier
    for entry in entries:
        # Every string is translatable and falls back to English, so English is required.
        assert entry.get('en'), (identifier, entry)
        for language, text in entry.items():
            assert language in languages, (identifier, language)
            assert text.strip() == text and text, (identifier, language)
    for step in chapter['steps']:
        image = step.get('image')
        if image is None:
            continue
        assert not image.startswith('/') and '..' not in image, image
        assert (ROOT / 'manual' / image).is_file(), image

print(f"PASS manual: {len(manual['chapters'])} chapters, "
      f"{sum(len(chapter['steps']) for chapter in manual['chapters'])} steps, "
      f"{len(languages)} languages")
sys.exit(0)
