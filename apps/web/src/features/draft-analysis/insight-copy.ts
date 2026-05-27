import type { Language } from "@/features/language/language-types";
import type {
  InsightConfidence,
  InsightSeverity,
} from "./draft-analysis-types";

type Bilingual<T extends string> = Record<Language, Record<T, string>>;

export const INSIGHTS_HEADING: Record<Language, string> = {
  en: "Notes",
  es: "Notas",
};

export const NO_INSIGHTS_COPY: Record<Language, string> = {
  en: "Nothing standing out right now.",
  es: "Nada destacable por ahora.",
};

export const JUMP_LABEL: Record<Language, string> = {
  en: "Jump",
  es: "Ir",
};

export const SECTION_ANCHOR_LABEL: Record<Language, string> = {
  en: "Section",
  es: "Sección",
};

export const DRAFT_ANCHOR_LABEL: Record<Language, string> = {
  en: "Whole draft",
  es: "Borrador completo",
};

export const EVIDENCE_REVEAL_LABEL: Record<Language, string> = {
  en: "Why?",
  es: "¿Por qué?",
};

export const EVIDENCE_HIDE_LABEL: Record<Language, string> = {
  en: "Hide",
  es: "Ocultar",
};

export const SEVERITY_LABEL: Bilingual<InsightSeverity> = {
  en: { info: "info", low: "soft", medium: "notable", high: "strong" },
  es: { info: "info", low: "suave", medium: "notable", high: "fuerte" },
};

export const CONFIDENCE_LABEL: Bilingual<InsightConfidence> = {
  en: { high: "high confidence", medium: "likely", low: "tentative" },
  es: { high: "alta confianza", medium: "probable", low: "tentativo" },
};

export const FILTER_ALL_LABEL: Record<Language, string> = {
  en: "All",
  es: "Todas",
};

export const FILTER_STRONG_LABEL: Record<Language, string> = {
  en: "Strong",
  es: "Fuertes",
};

export const SHOW_MORE_LABEL = (n: number): Record<Language, string> => ({
  en: `Show ${n} more`,
  es: `Mostrar ${n} más`,
});

export const SHOW_LESS_LABEL: Record<Language, string> = {
  en: "Show fewer",
  es: "Mostrar menos",
};
