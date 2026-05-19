import type { Language } from "@/features/language/language-types";

export interface Draft {
  id: string;
  title: string;
  content: string;
  language: Language;
  createdAt: string;
  updatedAt: string;
}

export interface DraftSummary {
  id: string;
  title: string;
  language: Language;
  updatedAt: string;
}

export type SaveStatus = "idle" | "dirty" | "saving" | "saved" | "offline";

export interface ServerDraftPayload {
  id: string;
  title: string;
  content: string;
  language?: string;
  created_at: string;
  updated_at: string;
}
