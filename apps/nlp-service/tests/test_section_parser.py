from app.domain.draft_analysis.section_parser import parse_sections


def test_blank_line_stanza_fallback() -> None:
    content = "line one\nline two\n\nline three\nline four"
    sections = parse_sections(content)
    assert len(sections) == 2
    assert [s.id for s in sections] == ["sec_1", "sec_2"]
    assert [s.label for s in sections] == [None, None]
    assert [ln.index for ln in sections[0].lines] == [1, 2]
    assert [ln.index for ln in sections[1].lines] == [4, 5]
    assert sections[0].line_start == 1 and sections[0].line_end == 2
    assert sections[1].line_start == 4 and sections[1].line_end == 5


def test_inline_labels_define_sections() -> None:
    content = "intro line\n[verse]\nverse line one\nverse line two\n[chorus]\nchorus line one\nchorus line two"
    sections = parse_sections(content)
    assert [s.label for s in sections] == [None, "verse", "chorus"]
    # The pre-label intro becomes its own section.
    assert sections[0].lines[0].text == "intro line"
    assert [ln.text for ln in sections[1].lines] == ["verse line one", "verse line two"]
    assert [ln.text for ln in sections[2].lines] == ["chorus line one", "chorus line two"]
    # Bracket lines themselves are excluded from per-section lines.
    assert all(not ln.text.startswith("[") for s in sections for ln in s.lines)


def test_explicit_sections_take_precedence() -> None:
    content = "[verse]\nignored A\nignored B\n[chorus]\nignored C"
    explicit = [("custom_1", "verse", 2, 3)]
    sections = parse_sections(content, explicit)
    assert len(sections) == 1
    assert sections[0].id == "custom_1"
    assert sections[0].label == "verse"
    assert [ln.index for ln in sections[0].lines] == [2, 3]
    assert [ln.text for ln in sections[0].lines] == ["ignored A", "ignored B"]


def test_explicit_section_skips_blank_and_label_lines() -> None:
    content = "first\n[chorus]\nhook one\n\nhook two"
    explicit = [("s", "chorus", 1, 5)]
    sections = parse_sections(content, explicit)
    assert len(sections) == 1
    assert [ln.index for ln in sections[0].lines] == [1, 3, 5]


def test_single_section_when_no_blanks_or_labels() -> None:
    sections = parse_sections("only one\nanother line")
    assert len(sections) == 1
    assert sections[0].line_start == 1
    assert sections[0].line_end == 2


def test_unknown_bracket_token_is_treated_as_lyric() -> None:
    sections = parse_sections("hey [name] of mine\nsecond line")
    assert len(sections) == 1
    assert sections[0].lines[0].text == "hey [name] of mine"


def test_label_case_insensitive_and_pre_chorus() -> None:
    content = "[Pre-Chorus]\nbuild up\n[CHORUS]\nbig moment"
    sections = parse_sections(content)
    assert [s.label for s in sections] == ["pre-chorus", "chorus"]
