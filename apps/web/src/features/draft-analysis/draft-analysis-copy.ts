import type { Language } from "@/features/language/language-types";
import type {
  CapabilityKey,
  CapabilityLevel,
  DraftAnalysisStatus,
} from "./draft-analysis-types";

type Bilingual = Record<Language, string>;

export const RAIL_TITLE: Bilingual = {
  en: "In the margin",
  es: "Al margen",
};

export const LINE_TAB_LABEL: Bilingual = {
  en: "Line",
  es: "Línea",
};

export const STRUCTURE_TAB_LABEL: Bilingual = {
  en: "Structure",
  es: "Estructura",
};

export const INSIGHTS_TAB_LABEL: Bilingual = {
  en: "Insights",
  es: "Hallazgos",
};

export const AT_A_GLANCE_HEADING: Bilingual = {
  en: "At a glance",
  es: "De un vistazo",
};

export const AT_A_GLANCE_SUMMARY: Record<
  Language,
  (sections: number, lines: number, syllables: number) => string
> = {
  en: (sections, lines, syllables) => {
    const lineWord = `${lines} line${lines === 1 ? "" : "s"}`;
    const syllableWord = `${syllables} syllable${syllables === 1 ? "" : "s"}`;
    return sections > 1
      ? `${lineWord} across ${sections} sections, ${syllableWord} total.`
      : `${lineWord}, ${syllableWord} total.`;
  },
  es: (sections, lines, syllables) => {
    const lineWord = `${lines} línea${lines === 1 ? "" : "s"}`;
    const syllableWord = `${syllables} sílaba${syllables === 1 ? "" : "s"}`;
    return sections > 1
      ? `${lineWord} en ${sections} secciones, ${syllableWord} en total.`
      : `${lineWord}, ${syllableWord} en total.`;
  },
};

export const AT_A_GLANCE_SCHEME_NOTE: Record<Language, (scheme: string) => string> = {
  en: (scheme) => `Mostly rhymes in ${scheme}.`,
  es: (scheme) => `Rima sobre todo en ${scheme}.`,
};

export const AT_A_GLANCE_CADENCE_NOTE: Record<"consistent" | "varied", Bilingual> = {
  consistent: {
    en: "Line lengths stay even throughout.",
    es: "La duración de las líneas se mantiene uniforme.",
  },
  varied: {
    en: "Line lengths vary widely.",
    es: "La duración de las líneas varía mucho.",
  },
};

export const LINE_NOTE_HEADING: Bilingual = {
  en: "A note on this line",
  es: "Una nota sobre esta línea",
};

export const SYLLABLES_ON_LINE_LABEL: Bilingual = {
  en: "syllables on this line",
  es: "sílabas en esta línea",
};

export const FIND_WEAK_LINE_LABEL: Bilingual = {
  en: "Find a line that's not pulling weight →",
  es: "Encuentra una línea que no aporta →",
};

export const ADD_SECTION_LABEL: Bilingual = {
  en: "+ Section",
  es: "+ Sección",
};

export const NO_LINE_COPY: Bilingual = {
  en: "Put the caret on a line to see its counts.",
  es: "Coloca el cursor en una línea para ver sus cuentas.",
};

export const REFRESH_LABEL: Bilingual = {
  en: "Refresh",
  es: "Actualizar",
};

export const COLLAPSE_LABEL: Bilingual = {
  en: "Hide review",
  es: "Ocultar revisión",
};

export const EXPAND_LABEL: Bilingual = {
  en: "Show review",
  es: "Mostrar revisión",
};

export const EMPTY_DRAFT_COPY: Bilingual = {
  en: "Write a few lines, then I'll have something to review.",
  es: "Escribe unas líneas y tendré algo que revisar.",
};

export const SUMMARY_HEADING: Bilingual = {
  en: "Overview",
  es: "Resumen",
};

export const SECTIONS_HEADING: Bilingual = {
  en: "Sections",
  es: "Secciones",
};

export const STANZAS_HEADING: Bilingual = {
  en: "Stanzas",
  es: "Estrofas",
};

export const NO_PATTERNS_COPY: Bilingual = {
  en: "No standout patterns yet.",
  es: "Aún no hay patrones destacados.",
};

export const NO_SECTIONS_COPY: Bilingual = {
  en: "No sections detected. Try adding blank lines between stanzas.",
  es: "No se detectaron secciones. Prueba a dejar líneas en blanco entre estrofas.",
};

export const JUMP_TO_LABEL: Bilingual = {
  en: "Jump to lines",
  es: "Ir a las líneas",
};

export const LOADING_COPY: Bilingual = {
  en: "Reading your draft…",
  es: "Leyendo tu borrador…",
};

export const CADENCE_LABEL: Bilingual = {
  en: "Cadence",
  es: "Cadencia",
};

export const SYLLABLES_LABEL: Bilingual = {
  en: "Syllables",
  es: "Sílabas",
};

export const VARIANCE_LABEL: Bilingual = {
  en: "Variance",
  es: "Varianza",
};

export const CONFIDENCE_LABEL: Bilingual = {
  en: "Confidence",
  es: "Confianza",
};

export const REPETITION_LABEL: Bilingual = {
  en: "Repetition",
  es: "Repetición",
};

export const RHYME_SCHEME_CONFIDENCE_LABEL: Record<"full" | "partial", Bilingual> = {
  full: { en: "Full", es: "Total" },
  partial: { en: "Partial", es: "Parcial" },
};

export const STATUS_COPY: Record<DraftAnalysisStatus, Bilingual> = {
  idle: {
    en: "Ready",
    es: "Listo",
  },
  loading: {
    en: "Analyzing…",
    es: "Analizando…",
  },
  fresh: {
    en: "Up to date",
    es: "Al día",
  },
  stale: {
    en: "Edits since last review",
    es: "Cambios sin revisar",
  },
  error: {
    en: "Couldn't analyze",
    es: "No se pudo analizar",
  },
  unsupported: {
    en: "Limited for this language",
    es: "Soporte limitado para este idioma",
  },
};

export const ERROR_HINT: Bilingual = {
  en: "Try again in a moment — your writing is safe.",
  es: "Inténtalo de nuevo en un momento; tu texto está a salvo.",
};

export const STALE_HINT: Bilingual = {
  en: "Refresh when you'd like a fresh look.",
  es: "Actualiza cuando quieras una nueva revisión.",
};

const CAPABILITY_LABELS: Record<CapabilityKey, Bilingual> = {
  rhymeScheme: { en: "Rhyme scheme", es: "Esquema de rima" },
  cadencePatterns: { en: "Cadence", es: "Cadencia" },
  stressHints: { en: "Stress hints", es: "Acentos" },
  repetition: { en: "Repetition", es: "Repetición" },
  mixedLanguage: { en: "Mixed language", es: "Idioma mixto" },
};

const CAPABILITY_LEVEL_LABEL: Record<CapabilityLevel, Bilingual> = {
  full: { en: "supported", es: "compatible" },
  partial: { en: "limited", es: "limitado" },
  unsupported: { en: "not available", es: "no disponible" },
};

export function capabilityLabel(
  key: CapabilityKey,
  language: Language,
): string {
  return CAPABILITY_LABELS[key][language];
}

export function capabilityLevelLabel(
  level: CapabilityLevel,
  language: Language,
): string {
  return CAPABILITY_LEVEL_LABEL[level][language];
}

export const SECTION_LABEL_PRESETS: Record<Language, readonly string[]> = {
  en: ["Verse", "Pre-Chorus", "Chorus", "Bridge", "Outro", "Hook", "Intro"],
  es: ["Verso", "Pre-Coro", "Coro", "Puente", "Outro", "Gancho", "Intro"],
};

export const ASSIGN_SECTION_LABEL: Bilingual = {
  en: "Label section",
  es: "Etiquetar sección",
};

export const CLEAR_SECTION_LABEL: Bilingual = {
  en: "Clear label",
  es: "Quitar etiqueta",
};

export const CUSTOM_LABEL_PLACEHOLDER: Bilingual = {
  en: "Custom label…",
  es: "Etiqueta personalizada…",
};
