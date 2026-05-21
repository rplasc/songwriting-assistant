import type { Language } from "@/features/language/language-types";
import type {
  DraftSection,
  ServerDraftSectionPayload,
} from "@/features/structure/structure-types";

export interface Draft {
  id: string;
  title: string;
  content: string;
  language: Language;
  sections: DraftSection[];
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface DraftSummary {
  id: string;
  title: string;
  language: Language;
  updatedAt: string;
}

/**
 * Save lifecycle states surfaced to the UI.
 *
 * - "offline": transient network failure, currently retrying.
 * - "conflict": server rejected because the draft was edited elsewhere.
 *   Terminal until the user reloads or chooses to overwrite.
 * - "error": non-recoverable failure after retry budget was spent, or
 *   the draft no longer exists on the server.
 */
export type SaveStatus =
  | "idle"
  | "dirty"
  | "saving"
  | "saved"
  | "offline"
  | "conflict"
  | "error";

export interface ServerDraftPayload {
  id: string;
  title: string;
  content: string;
  language?: string;
  sections?: ServerDraftSectionPayload[];
  version: number;
  created_at: string;
  updated_at: string;
}
