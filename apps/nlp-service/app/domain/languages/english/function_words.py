"""Closed-class English function words used by phrase-ending extraction.

Listed lowercased. Tokens enter the phrase-ending extractor in the form
produced by :func:`app.domain.normalization.normalize_word`, which keeps
internal apostrophes intact (so "don't" stays "don't"); contraction forms
are listed accordingly.

A word appears here when it carries little independent semantic weight at
the end of a sung phrase. The extractor uses this set to strip *leading*
function words from a trailing window so endings like "in the night" cap
to "night". Trailing function words inside the window (e.g. the "me" in
"hold me") are kept because they contribute phonetic material to the
ending.
"""

from __future__ import annotations

ENGLISH_FUNCTION_WORDS: frozenset[str] = frozenset(
    {
        # Articles & determiners
        "a", "an", "the", "this", "that", "these", "those", "such",
        "some", "any", "no", "every", "all", "each", "both", "either",
        "neither", "another", "other", "much", "many", "few",
        # Pronouns (subject, object, possessive, reflexive, wh-)
        "i", "you", "he", "she", "it", "we", "they",
        "me", "him", "her", "us", "them",
        "my", "your", "his", "its", "our", "their",
        "mine", "yours", "hers", "ours", "theirs",
        "myself", "yourself", "himself", "herself", "itself",
        "ourselves", "yourselves", "themselves",
        "who", "whom", "whose", "which", "what",
        # Auxiliaries and modals (bare forms)
        "am", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "having",
        "do", "does", "did", "doing", "done",
        "will", "would", "shall", "should", "may", "might", "must",
        "can", "could", "ought",
        # Common contractions (apostrophe preserved by normalize_word)
        "i'm", "i've", "i'll", "i'd",
        "you're", "you've", "you'll", "you'd",
        "he's", "he'll", "he'd",
        "she's", "she'll", "she'd",
        "it's", "it'll",
        "we're", "we've", "we'll", "we'd",
        "they're", "they've", "they'll", "they'd",
        "that's", "that'll",
        "there's", "here's", "what's", "who's", "where's", "how's",
        "let's",
        "don't", "doesn't", "didn't",
        "isn't", "aren't", "wasn't", "weren't",
        "haven't", "hasn't", "hadn't",
        "won't", "wouldn't", "shouldn't", "couldn't", "can't", "mustn't",
        "would've", "should've", "could've", "might've", "must've",
        # Prepositions
        "of", "in", "on", "at", "by", "to", "from", "with", "without",
        "for", "about", "into", "onto", "through", "over", "under",
        "above", "below", "between", "among", "around", "near", "off",
        "up", "down", "out", "across", "against", "along", "behind",
        "beside", "beyond", "during", "except", "inside", "outside",
        "since", "toward", "towards", "until", "upon", "within",
        # Conjunctions / subordinators
        "and", "or", "but", "nor", "yet", "so", "if", "than", "then",
        "because", "although", "though", "while", "whereas", "unless",
        "whether", "as", "when", "where", "why", "how",
        # Negation / affirmation
        "not", "yes",
        # Light discourse particles
        "just", "even", "still", "only", "also", "too",
    }
)
