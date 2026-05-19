import type { Language } from "./language-types";

export interface LanguageOption {
  value: Language;
  nativeLabel: string;
}

export const LANGUAGE_OPTIONS: ReadonlyArray<LanguageOption> = [
  { value: "en", nativeLabel: "English" },
  { value: "es", nativeLabel: "Español" },
];

export function languageOption(value: Language): LanguageOption {
  return (
    LANGUAGE_OPTIONS.find((o) => o.value === value) ?? LANGUAGE_OPTIONS[0]
  );
}
