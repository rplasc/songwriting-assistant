from app.domain.draft_analysis.cadence_rules import classify_pattern


def test_empty_input() -> None:
    result = classify_pattern([])
    assert result.cadence_class == "consistent"
    assert result.variance == 0.0
    assert result.severity == "low"


def test_single_line_is_consistent() -> None:
    result = classify_pattern([8])
    assert result.cadence_class == "consistent"


def test_consistent_when_stdev_and_spread_low() -> None:
    result = classify_pattern([8, 9, 8, 9])
    assert result.cadence_class == "consistent"
    assert result.severity == "low"


def test_varied_when_stdev_large() -> None:
    result = classify_pattern([4, 10, 5, 12])
    assert result.cadence_class == "varied"
    assert result.severity == "medium"


def test_mixed_in_between() -> None:
    # stdev between 1.0 and 2.5 OR spread > 2 with small stdev.
    result = classify_pattern([7, 8, 10, 11])
    assert result.cadence_class == "mixed"
    assert result.severity == "info"


def test_label_appears_in_message() -> None:
    result = classify_pattern([8, 8, 8], label="chorus")
    assert "Chorus" in result.message
