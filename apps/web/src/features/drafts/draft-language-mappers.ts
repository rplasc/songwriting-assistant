import {
  coerceLanguage,
  type Language,
} from "@/features/language/language-types";
import type { ServerDraftPayload } from "./drafts-types";

export function languageFromServer(payload: ServerDraftPayload): Language {
  return coerceLanguage(payload.language);
}
