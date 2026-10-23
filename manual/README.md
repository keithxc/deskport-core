# Shared manual

`manual.json` is the user manual that ships inside every DeskPort package. The
desktop app and the mobile clients read this one file; nothing is fetched at
runtime, so the manual always matches the installed version.

Edit the chapter structure in `i18n/manual.json` and the English-keyed text in
`i18n/strings.json`, then run `python3 i18n/generate_manual.py`. The file in
this directory is generated. Desktop-only sections explicitly name their
platform so the same manual remains useful to mobile readers.

## Format

```json
{
  "version": 1,
  "languages": ["en", "..."],
  "chapters": [
    { "id": "about",
      "title": {"en": "...", "zh-Hans": "..."},
      "steps": [ {"text": {"en": "..."}, "image": "images/about-devices.png"} ] }
  ]
}
```

- `id` is stable and never translated; clients may use it to link to a chapter.
- `title` and `step.text` hold one entry per language. A missing language falls
  back to another variant of the same language first (Traditional Chinese uses
  Simplified before English) and then to `en`, so a partially translated manual
  still renders in a related language.
- `image` is optional and relative to this directory. Images are bundled with the
  manual; they must not contain personal device names, addresses or private
  screen content.
- Clients show the chapters in file order, collapsed, one open at a time.

Language codes follow the mobile clients: `en`, `zh-Hans`, `zh-Hant`, `ja`, plus
the desktop's `ko`, `de`, `fr` and `es`. The desktop maps its catalog names
(`zh_CN`, `zh_TW`) onto `zh-Hans` and `zh-Hant`.

The text is user documentation, not protocol. Keep steps short, describe what
the person does, and avoid naming personal hosts or internal endpoints.
