from app.domain.languages.spanish.g2p import g2p


def test_corazon_phonemes() -> None:
    pron = g2p("corazón")
    assert pron.syllables == 3
    assert pron.phonemes == ("K", "O0", "R", "A0", "S", "O1", "N")


def test_cancion_phonemes() -> None:
    pron = g2p("canción")
    # ca-n-ción: C A0 N S I0 O1 N
    assert pron.phonemes == ("K", "A0", "N", "S", "I0", "O1", "N")
    assert pron.syllables == 2


def test_yeismo_ll_becomes_y() -> None:
    pron = g2p("caballo")
    assert "Y" in pron.phonemes
    # Should NOT contain the Castilian LL/LY representation we don't use.
    assert all(p != "LY" for p in pron.phonemes)


def test_jota_g_before_front_vowel() -> None:
    pron_jamás = g2p("jamás")
    assert pron_jamás.phonemes[0] == "H"
    pron_gente = g2p("gente")
    assert pron_gente.phonemes[0] == "H"


def test_seseo_c_z_become_s() -> None:
    pron_cielo = g2p("cielo")
    assert pron_cielo.phonemes[0] == "S"
    pron_zapato = g2p("zapato")
    assert pron_zapato.phonemes[0] == "S"


def test_qu_collapses_to_k() -> None:
    pron = g2p("queso")
    assert pron.phonemes[0] == "K"
    # silent u: no U phoneme between K and E
    assert pron.phonemes[1] == "E1"


def test_silent_h() -> None:
    pron = g2p("hola")
    # h-o-l-a → O L A (stress on first syllable, llano with vowel ending)
    assert pron.phonemes[0] == "O1"


def test_n_tilde_becomes_ny() -> None:
    pron = g2p("año")
    assert "NY" in pron.phonemes


def test_initial_r_is_trill() -> None:
    pron = g2p("rojo")
    assert pron.phonemes[0] == "RR"


def test_intervocalic_r_is_tap() -> None:
    pron = g2p("caro")
    # K A1 R O0 — single tap.
    assert pron.phonemes == ("K", "A1", "R", "O0")


def test_rr_digraph_is_trill() -> None:
    pron = g2p("carro")
    assert "RR" in pron.phonemes
