import type { Language } from "@/features/language/language-types";
import type {
  AdvancedRhymeMode,
  AdvancedRhymeTargetType,
  EvidenceTag,
  RhymeConfidence,
  RhymeFamily,
} from "./advanced-rhyme-types";

type Bilingual<T extends string> = Record<Language, Record<T, string>>;

export const PANEL_TITLE: Record<Language, string> = {
  en: "Explore rhymes",
  es: "Explorar rimas",
};

export const CLOSE_LABEL: Record<Language, string> = {
  en: "Close",
  es: "Cerrar",
};

export const OPEN_LABEL: Record<Language, string> = {
  en: "Explore deeper",
  es: "Explorar más",
};

export const MODE_LABEL: Bilingual<AdvancedRhymeMode> = {
  en: {
    perfect: "Perfect",
    near: "Near",
    consonant: "Consonant",
    assonant: "Assonant",
    multisyllabic: "Multisyllabic",
  },
  es: {
    perfect: "Consonante",
    near: "Cercana",
    consonant: "Consonante",
    assonant: "Asonante",
    multisyllabic: "Multisilábica",
  },
};

export const TARGET_TYPE_LABEL: Bilingual<AdvancedRhymeTargetType> = {
  en: {
    word: "Word",
    phrase_ending: "Phrase ending",
  },
  es: {
    word: "Palabra",
    phrase_ending: "Final de frase",
  },
};

export const CONFIDENCE_LABEL: Bilingual<RhymeConfidence> = {
  en: { high: "Strong", medium: "Likely", low: "Soft" },
  es: { high: "Fuerte", medium: "Probable", low: "Suave" },
};

export const FAMILY_LABEL: Bilingual<RhymeFamily> = {
  en: {
    perfect: "perfect",
    multisyllabic: "multisyllabic",
    near: "near",
    assonant: "assonant",
    consonant: "consonant",
  },
  es: {
    perfect: "consonante",
    multisyllabic: "multisilábica",
    near: "cercana",
    assonant: "asonante",
    consonant: "consonante",
  },
};

export const EVIDENCE_LABEL: Bilingual<EvidenceTag> = {
  en: {
    shared_stressed_ending: "shared stressed ending",
    shared_vowel_pattern: "shared vowels",
    shared_consonant_tail: "shared consonant tail",
    phrase_ending_match: "phrase-ending match",
    heuristic_fallback: "approximate",
    multisyllabic_key_match: "multisyllabic key match",
  },
  es: {
    shared_stressed_ending: "terminación tónica compartida",
    shared_vowel_pattern: "vocales compartidas",
    shared_consonant_tail: "consonantes finales compartidas",
    phrase_ending_match: "coincidencia final de frase",
    heuristic_fallback: "aproximada",
    multisyllabic_key_match: "coincidencia multisilábica",
  },
};

export const EMPTY_COPY: Record<Language, string> = {
  en: "Type a line, then explore.",
  es: "Escribe una línea y luego explora.",
};

export const NO_RESULTS_COPY: Record<Language, string> = {
  en: "Nothing here — try a different mode or target.",
  es: "Nada por aquí — prueba otro modo o destino.",
};

export const LOADING_COPY: Record<Language, string> = {
  en: "exploring…",
  es: "explorando…",
};

export const ERROR_COPY: Record<Language, string> = {
  en: "Lost the connection.",
  es: "Se perdió la conexión.",
};

export const CAPABILITY_PARTIAL_COPY: Record<Language, string> = {
  en: "Multisyllabic matching is partial in this language — showing best approximations.",
  es: "El emparejamiento multisilábico es parcial en este idioma — mostrando aproximaciones.",
};

export const CAPABILITY_UNSUPPORTED_COPY: Record<Language, string> = {
  en: "Multisyllabic matching isn't supported here yet.",
  es: "El emparejamiento multisilábico no se admite aquí todavía.",
};

export const TARGET_TYPE_HEADER: Record<Language, string> = {
  en: "Target",
  es: "Destino",
};

export const MODE_HEADER: Record<Language, string> = {
  en: "Mode",
  es: "Modo",
};
