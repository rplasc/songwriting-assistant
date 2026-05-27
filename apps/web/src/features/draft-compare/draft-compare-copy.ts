import type { Language } from "@/features/language/language-types";

type Bilingual = Record<Language, string>;

export const COMPARE_HEADING: Bilingual = {
  en: "Compare",
  es: "Comparar",
};

export const SET_BASELINE_LABEL: Bilingual = {
  en: "Set baseline",
  es: "Fijar referencia",
};

export const CLEAR_BASELINE_LABEL: Bilingual = {
  en: "Clear baseline",
  es: "Quitar referencia",
};

export const COMPARE_NOW_LABEL: Bilingual = {
  en: "Compare now",
  es: "Comparar ahora",
};

export const RECOMPARE_LABEL: Bilingual = {
  en: "Recompare",
  es: "Comparar de nuevo",
};

export const BASELINE_NOT_SET_COPY: Bilingual = {
  en: "Set a baseline, then keep writing — I'll mark what shifts.",
  es: "Fija una referencia y sigue escribiendo — te diré qué cambia.",
};

export const BASELINE_READY_TO_COMPARE_COPY: Bilingual = {
  en: "Whenever you're ready, take a look.",
  es: "Cuando quieras, échale un vistazo.",
};

export const BASELINE_MATCHES_COPY: Bilingual = {
  en: "You're right at the baseline — keep going.",
  es: "Estás justo en la referencia — sigue.",
};

export const COMPARE_LOADING_COPY: Bilingual = {
  en: "comparing…",
  es: "comparando…",
};

export const COMPARE_ERROR_COPY: Bilingual = {
  en: "Couldn't compare.",
  es: "No se pudo comparar.",
};

export const BASELINE_EXPIRED_COPY: Bilingual = {
  en: "That baseline has drifted out of memory — set a new one.",
  es: "Esa referencia ya no está en memoria — fija una nueva.",
};

export const RESET_BASELINE_LABEL: Bilingual = {
  en: "Reset baseline",
  es: "Restablecer referencia",
};

export const BASELINE_FRESH_NOTE: Bilingual = {
  en: "Baseline set",
  es: "Referencia fijada",
};

export const BASELINE_STALE_NOTE: Bilingual = {
  en: "Baseline reflects an earlier draft",
  es: "La referencia refleja un borrador anterior",
};

export const NO_CHANGES_COPY: Bilingual = {
  en: "Not much has shifted since the baseline.",
  es: "No ha cambiado mucho desde la referencia.",
};

export const DELTA_LABEL = {
  en: {
    motifs: "motifs",
    repetition: "repetition",
    sections: "sections",
    consistency: "consistency",
  },
  es: {
    motifs: "motivos",
    repetition: "repetición",
    sections: "secciones",
    consistency: "consistencia",
  },
} as const;

export const COMPARE_SECTION_LABEL: Bilingual = {
  en: "compare insights",
  es: "comparativas",
};

export const CURRENT_SECTION_LABEL: Bilingual = {
  en: "current insights",
  es: "insights actuales",
};
