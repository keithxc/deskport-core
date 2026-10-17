# Local desktop text input

The desktop viewer may opt into its operating system's input method. This is a
client adapter option, independent of display policy and the remote host's input
method. Existing peers continue to use physical keyboard input by default.

Composition/preedit and candidate selection stay local. Only committed UTF-8
travels over the existing reliable Moonlight UTF-8 text input channel. No new
binding message or capability is required; no clipboard read/write is involved.
The host must already support that channel. Applications requiring hardware key
semantics, games and remote input methods should use physical input mode.

The initial desktop adapter does not subscribe to the optional text-caret
extension. Its candidate anchor is a fixed local top-left composition area,
never an inferred remote caret. The existing opt-in `text-caret` extension remains
unchanged. Future caret placement must validate freshness, lease scope, drawable
mapping, accessibility failure and unknown/invalid geometry before using it.

Hiding, losing routing focus, releasing capture or disconnecting cancels local
composition and releases remote keys. Cancelled, stale and other-window text
must not commit after reactivation. Text-producing physical keys and candidate
navigation must not be forwarded alongside committed text. Local input-method
switching chords stay local; explicit remote command chords remain available
outside composition. System shortcut capture is disabled in local text mode so
the client input method can receive its normal OS shortcuts.

Adapter checks must distinguish synthetic SDL event regression, a native IME
candidate/composition/commit session, and remote application acceptance. Text
pasting, binary compilation and physical key forwarding do not establish IME
acceptance. Native Chinese, Japanese and Korean checks must cover selection,
cancellation, dead keys/AltGr, long text, command chords, focus loss and hiding.
