"""Closed-class Spanish function words used by phrase-ending extraction.

Lowercased and accent-preserving, matching the form produced by
:func:`app.domain.languages.spanish.normalization.normalize_word`. The
extractor strips *leading* function words from a trailing window so an
ending like "en la noche" caps to "noche".
"""

from __future__ import annotations

SPANISH_FUNCTION_WORDS: frozenset[str] = frozenset(
    {
        # Artículos
        "el", "la", "los", "las",
        "un", "una", "unos", "unas",
        "lo",  # neutral article ("lo bueno")
        # Contracciones obligatorias (kept here too — sometimes survive
        # normalization if upstream code didn't expand them)
        "del", "al",
        # Pronombres personales (sujeto)
        "yo", "tú", "tu", "él", "ella", "usted",
        "nosotros", "nosotras", "vosotros", "vosotras",
        "ellos", "ellas", "ustedes",
        # Pronombres átonos (objeto / reflexivo)
        "me", "te", "se", "nos", "os",
        "lo", "la", "los", "las", "le", "les",
        # Pronombres posesivos / demostrativos cortos
        "mi", "mis", "tu", "tus", "su", "sus",
        "mío", "mía", "míos", "mías",
        "tuyo", "tuya", "tuyos", "tuyas",
        "suyo", "suya", "suyos", "suyas",
        "nuestro", "nuestra", "nuestros", "nuestras",
        "vuestro", "vuestra", "vuestros", "vuestras",
        "este", "esta", "estos", "estas", "esto",
        "ese", "esa", "esos", "esas", "eso",
        "aquel", "aquella", "aquellos", "aquellas", "aquello",
        # Preposiciones
        "a", "ante", "bajo", "con", "contra", "de", "desde", "durante",
        "en", "entre", "hacia", "hasta", "mediante", "para", "por",
        "según", "sin", "so", "sobre", "tras", "versus", "vía",
        # Conjunciones / nexos comunes
        "y", "e", "o", "u", "ni", "pero", "sino", "aunque", "porque",
        "pues", "como", "cuando", "donde", "mientras", "si", "que",
        "ya", "aún", "todavía",
        # Interrogativos y relativos
        "qué", "quién", "quiénes", "cuál", "cuáles", "cómo",
        "cuándo", "dónde", "por qué", "cuánto", "cuánta",
        "cuántos", "cuántas",
        # Negación / afirmación
        "no", "ni", "sí",
        # Partículas frecuentes en letras
        "muy", "más", "menos", "tan", "tanto", "solo", "sólo",
        "también", "tampoco",
    }
)
