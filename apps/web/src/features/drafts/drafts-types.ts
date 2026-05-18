export interface Draft {
  id: string;
  title: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

export interface DraftSummary {
  id: string;
  title: string;
  updatedAt: string;
}

export type SaveStatus = "idle" | "dirty" | "saving" | "saved" | "offline";

export interface ServerDraftPayload {
  id: string;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}
