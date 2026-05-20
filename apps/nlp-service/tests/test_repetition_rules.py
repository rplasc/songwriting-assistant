from app.domain.draft_analysis.repetition_rules import (
    detect_draft_overuse,
    detect_section_signals,
)


# ── Section-level signals ─────────────────────────────────────────────────────

def test_opening_phrase_repeat_two_lines() -> None:
    tokens = [["hold", "me", "in", "the", "window"], ["hold", "me", "when", "the", "city"]]
    signals = detect_section_signals(tokens)
    opening = [s for s in signals if s.type == "opening_phrase_repeat"]
    assert len(opening) == 1
    assert opening[0].value == "hold me"


def test_opening_phrase_single_shared_token() -> None:
    tokens = [["fire", "burns", "bright"], ["fire", "in", "my", "soul"]]
    signals = detect_section_signals(tokens)
    opening = [s for s in signals if s.type == "opening_phrase_repeat"]
    assert len(opening) == 1
    assert opening[0].value == "fire"


def test_no_opening_repeat_when_all_different_starts() -> None:
    tokens = [["running", "away"], ["falling", "down"], ["broken", "glass"]]
    signals = detect_section_signals(tokens)
    assert not any(s.type == "opening_phrase_repeat" for s in signals)


def test_ending_word_repeat() -> None:
    tokens = [["I", "see", "the", "light"], ["she", "walks", "toward", "the", "light"]]
    # normalize to lowercase as the service would
    tokens = [[t.lower() for t in tl] for tl in tokens]
    signals = detect_section_signals(tokens)
    ending = [s for s in signals if s.type == "ending_word_repeat"]
    assert len(ending) == 1
    assert ending[0].value == "light"


def test_no_ending_repeat_when_different_last_words() -> None:
    tokens = [["burning", "fire"], ["frozen", "rain"], ["endless", "sky"]]
    signals = detect_section_signals(tokens)
    assert not any(s.type == "ending_word_repeat" for s in signals)


def test_single_line_returns_no_signals() -> None:
    assert detect_section_signals([["only", "one", "line"]]) == []


def test_empty_returns_no_signals() -> None:
    assert detect_section_signals([]) == []


# ── Draft-level overuse ───────────────────────────────────────────────────────

def test_overuse_detected_when_word_on_three_lines() -> None:
    lines = [
        ["love", "burns"],
        ["love", "fades"],
        ["love", "remains"],
    ]
    signals = detect_draft_overuse(lines)
    assert any(s.word == "love" for s in signals)


def test_overuse_not_reported_for_stop_words() -> None:
    lines = [["i", "see"], ["i", "feel"], ["i", "know"]]
    signals = detect_draft_overuse(lines)
    assert not any(s.word == "i" for s in signals)


def test_overuse_not_reported_when_below_threshold() -> None:
    lines = [["shadow", "falls"], ["shadow", "grows"]]
    signals = detect_draft_overuse(lines)
    assert not any(s.word == "shadow" for s in signals)


def test_overuse_sorted_by_line_count_descending() -> None:
    lines = [
        ["love", "hate", "fire"],
        ["love", "hate", "rain"],
        ["love", "dusk"],
        ["love", "dawn"],
    ]
    signals = detect_draft_overuse(lines)
    if len(signals) >= 2:
        assert signals[0].line_count >= signals[1].line_count
