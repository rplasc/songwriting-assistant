"""Orchestrates lemma-based semantic analysis for a draft.

Sits beside the Phase 4 ``DraftAnalysisService``. The draft service calls
``DraftNlpService.analyze`` after literal-repetition rules when the
caller opts in via ``DraftAnalysisOptions``. Stateless aside from the
language→lemmatizer registry built at startup.

This service deliberately stays a thin compose layer:
- pull per-line lemmas using the per-language lemmatizer,
- build PhraseRefs (function-words stripped) and LemmaLocations,
- delegate to phrase_clustering, semantic_repetition_rules,
  motif_tracker, section_contrast_rules and consistency_rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.draft_analysis.consistency_rules import (
    ConsistencyDriftInsight,
    detect_perspective_drift,
    detect_tense_drift,
)
from app.domain.draft_analysis.motif_tracker import MotifInsight, track_motifs
from app.domain.draft_analysis.section_contrast_rules import (
    SectionContrastInsight,
    detect_section_contrast,
)
from app.domain.draft_analysis.section_parser import ParsedSection
from app.domain.draft_analysis.semantic_repetition_rules import (
    SemanticRepetitionInsight,
    detect_semantic_repetition,
)
from app.domain.languages.english.function_words import ENGLISH_FUNCTION_WORDS
from app.domain.languages.spanish.function_words import SPANISH_FUNCTION_WORDS
from app.domain.nlp.content import content_lemmas
from app.domain.nlp.lemmatization import Lemmatizer, SimplemmaLemmatizer
from app.domain.nlp.motif_rules import LemmaLocation
from app.domain.nlp.perspective import classify_person
from app.domain.nlp.phrase_clustering import PhraseCluster, PhraseRef, cluster_phrases
from app.domain.nlp.tense import classify_tense
from app.models.token import Token


_FUNCTION_WORDS: dict[str, frozenset[str]] = {
    "en": ENGLISH_FUNCTION_WORDS,
    "es": SPANISH_FUNCTION_WORDS,
}

_MAX_CONTENT_LEMMAS_PER_LINE = 6

# M4 consistency_hints umbrella capability per language. ES tense
# detection leans on suffix heuristics with known irregular gaps; the
# umbrella label reflects the weakest sub-feature.
_CONSISTENCY_CAPABILITY: dict[str, str] = {"en": "full", "es": "partial"}


@dataclass(frozen=True, slots=True)
class DraftNlpResult:
    motifs: list[str]
    semantic_repetition: list[SemanticRepetitionInsight]
    motif_insights: list[MotifInsight]
    section_contrast: list[SectionContrastInsight] = field(default_factory=list)
    consistency: list[ConsistencyDriftInsight] = field(default_factory=list)
    # Lemmas that the overuse pass flagged whose occurrences are entirely
    # confined to hook-labeled sections. Surfaces here so hook_demotion
    # can act on draft-scoped word_overuse insights without re-walking
    # tokens.
    hook_only_overuse_words: frozenset[str] = frozenset()
    # Per-language consistency capability label so the caller can flip
    # the umbrella field without re-deriving it.
    consistency_capability: str = "unsupported"


class DraftNlpService:
    """One instance per app; holds a SimplemmaLemmatizer per language."""

    def __init__(self, lemmatizers: dict[str, Lemmatizer] | None = None) -> None:
        self._lemmatizers: dict[str, Lemmatizer] = lemmatizers or {
            "en": SimplemmaLemmatizer("en"),
            "es": SimplemmaLemmatizer("es"),
        }

    def supports(self, language: str) -> bool:
        return language in self._lemmatizers

    def analyze(
        self,
        language: str,
        sections: list[ParsedSection],
        line_token_objects: dict[str, list[list[Token]]],
        include_semantic_repetition: bool,
        include_motif_tracking: bool,
        include_section_contrast: bool = False,
        include_consistency_hints: bool = False,
    ) -> DraftNlpResult:
        """Run the semantic pipeline.

        ``line_token_objects`` is keyed by section id and holds the same
        Token lists the Phase 4 path already produced — we reuse them to
        avoid re-tokenizing.
        """
        lemmatizer = self._lemmatizers.get(language)
        if lemmatizer is None:
            return DraftNlpResult([], [], [])

        function_words = _FUNCTION_WORDS.get(language, frozenset())

        phrases: list[PhraseRef] = []
        locations: list[LemmaLocation] = []
        section_bags: dict[str, set[str]] = {}
        section_endings: dict[str, list[str]] = {}
        for section in sections:
            tokens_per_line = line_token_objects.get(section.id, [])
            bag: set[str] = set()
            endings: list[str] = []
            for parsed_line, tokens in zip(section.lines, tokens_per_line):
                line_lemmas = content_lemmas(tokens, lemmatizer, function_words)
                if tokens:
                    last_norm = tokens[-1].normalized
                    if last_norm:
                        endings.append(lemmatizer.lemmatize_word(last_norm))
                if not line_lemmas:
                    continue
                bag.update(line_lemmas)
                for lemma in line_lemmas:
                    locations.append(
                        LemmaLocation(
                            section_id=section.id,
                            line_index=parsed_line.index,
                            lemma=lemma,
                        )
                    )
                phrases.append(
                    PhraseRef(
                        section_id=section.id,
                        line_index=parsed_line.index,
                        text=parsed_line.text,
                        lemmas=tuple(line_lemmas[:_MAX_CONTENT_LEMMAS_PER_LINE]),
                    )
                )
            section_bags[section.id] = bag
            section_endings[section.id] = endings

        semantic: list[SemanticRepetitionInsight] = []
        if include_semantic_repetition and phrases:
            clusters: list[PhraseCluster] = cluster_phrases(phrases)
            semantic = detect_semantic_repetition(clusters)

        motifs: list[str] = []
        motif_insights: list[MotifInsight] = []
        if include_motif_tracking and locations:
            motifs, motif_insights = track_motifs(locations, function_words)

        contrast: list[SectionContrastInsight] = []
        if include_section_contrast and len(sections) >= 2:
            contrast = detect_section_contrast(sections, section_bags, section_endings)

        consistency: list[ConsistencyDriftInsight] = []
        consistency_capability = "unsupported"
        if include_consistency_hints:
            consistency_capability = _CONSISTENCY_CAPABILITY.get(
                language, "unsupported"
            )
            persons = _classify_sections(
                sections, line_token_objects, language, classify_person
            )
            tenses = _classify_sections(
                sections, line_token_objects, language, classify_tense
            )
            consistency.extend(detect_perspective_drift(sections, persons))
            consistency.extend(detect_tense_drift(sections, tenses, language))

        hook_only_overuse = _hook_only_overuse_lemmas(sections, locations)

        return DraftNlpResult(
            motifs=motifs,
            semantic_repetition=semantic,
            motif_insights=motif_insights,
            section_contrast=contrast,
            consistency=consistency,
            hook_only_overuse_words=hook_only_overuse,
            consistency_capability=consistency_capability,
        )


_HOOK_LABELS: frozenset[str] = frozenset({"chorus", "hook", "refrain"})


def _classify_sections(
    sections: list[ParsedSection],
    line_token_objects: dict[str, list[list[Token]]],
    language: str,
    classifier,
) -> dict[str, list[tuple[int, str]]]:
    out: dict[str, list[tuple[int, str]]] = {}
    for section in sections:
        items: list[tuple[int, str]] = []
        tokens_per_line = line_token_objects.get(section.id, [])
        for parsed_line, tokens in zip(section.lines, tokens_per_line):
            for token in tokens:
                label = classifier(token.normalized, language)
                if label is not None:
                    items.append((parsed_line.index, label))
        out[section.id] = items
    return out


def _hook_only_overuse_lemmas(
    sections: list[ParsedSection],
    locations: list[LemmaLocation],
) -> frozenset[str]:
    hook_ids = {s.id for s in sections if s.label in _HOOK_LABELS}
    if not hook_ids:
        return frozenset()
    by_lemma_sections: dict[str, set[str]] = {}
    for loc in locations:
        by_lemma_sections.setdefault(loc.lemma, set()).add(loc.section_id)
    return frozenset(
        lemma
        for lemma, section_set in by_lemma_sections.items()
        if section_set and section_set.issubset(hook_ids)
    )


__all__ = ["DraftNlpResult", "DraftNlpService"]
