# Shared UI localization

`languages.json` owns the shared language list, native names, resource locale
mapping and text direction. `strings.json` is the single table for all authored
DeskPort UI text, including platform-only text and the offline manual. English
originals are lookup IDs, never wire values. Language codes are columns;
`_platforms` records the desktop contexts and Apple/Android usage. An unused
platform has an empty list or `false`. Missing language cells fall back to English;
they are never filled with a guessed protocol value. No translation service or
network access is used at build time or runtime.

Consumers generate Qt TS/QM, Apple strings and Android XML resources. Their
checks reject missing required locales, changed placeholders and stale generated
resources. `qt.json` retains context, locations and catalog metadata; `_qt` cells
preserve existing translations where identical English has a different meaning
in a specific Qt context. `manual.json` stores manual structure and English IDs;
run `generate_manual.py` to regenerate the shipped manual. Call localization only at explicit UI boundaries
(`qsTr`, `QCoreApplication::translate`, `DPL`, `DPStrings.text`). Never translate
JSON keys, capabilities, message names, enum/storage IDs, command arguments,
addresses, server errors or user-provided text. Protocols and their fixtures are
unchanged by this module.

The initial table contains 1,019 English IDs imported from the existing DeskPort
Qt catalogs, DeskPort Client UI catalog and shared manual. Existing GPL-3.0-or-later notices and translation
provenance apply here; this directory is separate from the MIT `portable/`
module. It contains no mobile implementation, host data or credentials. Mobile
consumers load the `apple` / `android` table views; platform-only rows do not
appear in the other product's generated resources. Consumer updates can follow
independent release schedules without changing wire behavior.

The shared registry now includes 22 languages: English, both Chinese scripts,
Japanese, French, German, Arabic, Korean, Portuguese, Spanish, Tibetan, Italian,
Russian, Indonesian, Turkish, Vietnamese, Thai, Dutch, Polish, Ukrainian, Hindi
and Malay. Indonesian keeps the upstream Android `in` resource/picker code while
exposing canonical `id` to modern OS locale settings.

New translations added on 2026-10-17 are machine-assisted drafts with technical
tokens and format placeholders preserved. Common navigation terminology is
reviewed during integration; native-speaker review, especially Tibetan, and
physical-device font/layout acceptance remain open. Existing human translations
are retained where available. Portuguese uses the generic `pt` catalog, including
regional system-locale fallback. Tibetan uses `bo`; Arabic uses `ar` and RTL.

Run `python3 i18n/catalog.py` and `python3 tests/test_i18n.py` before advancing
consumer pins. Locale choice never changes any wire or stored protocol value.

## Custom desktop recall binding — 2026-10-24

The desktop shortcut recorder, validation hints and compositor-assigned binding
status have draft translations in all 22 primary locales. The offline manual
explains recording, saving, cancellation and restoring the default binding in
English and both Chinese scripts, with English fallback elsewhere. Binding
validation, storage and native registration stay in the desktop adapter.

The key chooser also has 22 locale drafts and complements recording when the
desktop reserves a combination. The manual identifies the current-binding
button on the single settings row and explains KDE Plasma's Meta+1–9 task-manager
shortcuts and desktop conflict confirmation. Historical catalog entries remain
available to consumers on older pins.

## Desktop shortcut and manual expansion — 2026-10-24

The desktop window-shortcut controls have draft translations in all 22 primary
locales. Expanded manual sections are authored in English, Simplified Chinese
and Traditional Chinese; other locales retain their existing translations and
use the documented English fallback for new paragraphs.

## Browser view — 2026-10-17

`_web: ["Browser"]` explicitly scopes Web UI usage without changing the native
`_platforms` schema. `_webTranslations.Browser` supplies a context-specific cell
when the generic row does not cover that language. Consumers project this view
and `languages.json` into static resources; English originals remain the IDs.
No browser dictionary is authored in the consumer and no mobile source is used.

The Web view contains 126 originals in all 22 primary locales. New Web-only
translations are machine-assisted drafts (including a one-time authoring import);
native-speaker review remains required, especially Tibetan and authentication
instructions. Existing native translations and native output are unchanged.
The authoring import is not a build or runtime dependency. Consumers retain an
explicit English fallback for absent cells and unsupported browser languages.
Error codes, settings IDs, user names, server messages and transmitted text are
not translation keys. Numbered placeholders must be preserved; consumers insert
values once as text and isolate bidirectional arguments.
