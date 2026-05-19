from app.domain.heuristic_g2p import heuristic_phoneme_tails


def test_returns_empty_when_no_vowel() -> None:
    assert heuristic_phoneme_tails("qzqzqz") == []
    assert heuristic_phoneme_tails("") == []


def test_magic_e_long_vowel() -> None:
    tails = heuristic_phoneme_tails("kite")
    assert ("AY1", "T") in tails


def test_magic_e_cute() -> None:
    tails = heuristic_phoneme_tails("cute")
    assert ("UW1", "T") in tails


def test_double_e_open_syllable() -> None:
    tails = heuristic_phoneme_tails("glee")
    assert ("IY1",) in tails


def test_single_vowel_end() -> None:
    tails = heuristic_phoneme_tails("thru")
    # 'u' as final vowel resolves to AH1 or UW1; UW1 is the relevant reading.
    assert any(t and t[0] in ("UW1", "AH1") for t in tails)


def test_misspelled_dactyl_has_al_tail() -> None:
    tails = heuristic_phoneme_tails("wundurful")
    # Last vowel cluster is 'u', tail is 'l' -> at least one candidate
    # should be AH1 + L (matches the AH0 L tail used by "wonderful" family).
    assert any(t == ("AH1", "L") for t in tails)


def test_r_colored_er() -> None:
    tails = heuristic_phoneme_tails("biggur")
    # 'u' + 'r' as the final vowel/tail -> ER1 should be among the candidates.
    assert any(t == ("ER1",) for t in tails)


def test_consonant_digraph_th_collapses() -> None:
    tails = heuristic_phoneme_tails("blath")
    # 'a' + 'th' -> some vowel + TH (single phoneme, not T+H).
    assert all(t[-1] == "TH" for t in tails if len(t) >= 2)


def test_doubled_consonant_collapses() -> None:
    tails = heuristic_phoneme_tails("buzz")
    # 'zz' should collapse to a single Z, so tails end with exactly one Z.
    for t in tails:
        assert t[-1] == "Z"
        assert t.count("Z") == 1


def test_returns_bounded_number_of_candidates() -> None:
    # Multi-reading vowel ('ou' has 4 candidates) plus stress expansion (3x)
    # plus 'gh' silent — still capped.
    tails = heuristic_phoneme_tails("nough")
    assert 0 < len(tails) <= 30


def test_candidates_are_deduplicated() -> None:
    tails = heuristic_phoneme_tails("ay")
    # All stress variants are still unique tuples.
    assert len(tails) == len(set(tails))


def test_syllabic_le_reanchors_to_inner_vowel() -> None:
    """Words ending in -Cle (glimble, fumble) reanchor on the vowel before the
    consonant cluster, with a syllabic AH0+L tail."""
    tails = heuristic_phoneme_tails("glimble")
    # Should include (IH1, M, B, AH0, L) — matches "thimble" perfect key.
    assert ("IH1", "M", "B", "AH0", "L") in tails
    # Family key for any of these tails is "AH0_L" — that's the win.
    assert all(t[-2:] == ("AH0", "L") for t in tails)


def test_stress_variants_emitted_for_each_vowel() -> None:
    """Every vowel candidate appears at stress levels 0, 1, and 2 so the
    final-syllable schwa patterns ('-ful'/'-ble'/'-ous') match."""
    tails = heuristic_phoneme_tails("wundurful")
    # AH0+L is what 'wonderful'/'beautiful' family-key on.
    assert ("AH0", "L") in tails
    assert ("AH1", "L") in tails
    assert ("AH2", "L") in tails


def test_oa_digraph_maps_to_ow() -> None:
    tails = heuristic_phoneme_tails("woah")
    # 'oa' -> OW1 (with stress variants); 'h' is silent.
    assert ("OW1",) in tails
    assert ("OW0",) in tails


def test_silent_trailing_h() -> None:
    """Trailing 'h' alone is silent: oh, ah, blah, yeah."""
    tails = heuristic_phoneme_tails("oh")
    # 'o' -> AA1/OW1/AO1; tail 'h' silent.
    assert any(t == ("OW1",) for t in tails)
    assert all(len(t) == 1 for t in tails)


def test_magic_e_soft_c_gives_s_not_k() -> None:
    """Before a silent 'e', 'c' is soft: blace/place/race → ...S, not ...K."""
    tails = heuristic_phoneme_tails("blace")
    assert any(t[-1] == "S" for t in tails), "expected S in tails"
    assert not any(t[-1] == "K" for t in tails), "unexpected K in tails"


def test_magic_e_soft_g_gives_jh_not_g() -> None:
    """Before a silent 'e', 'g' is soft: strage/stage/huge → ...JH, not ...G."""
    tails = heuristic_phoneme_tails("strage")
    assert any(t[-1] == "JH" for t in tails), "expected JH in tails"
    assert not any(t[-1] == "G" for t in tails), "unexpected G in tails"
