import type { DraftSummary } from "./drafts-types";

const RECENT_KEY = "sa.drafts.recent";
const CURRENT_KEY = "sa.drafts.current";
const MAX_RECENT = 10;

function safeLocalStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function getRecentDrafts(): DraftSummary[] {
  const storage = safeLocalStorage();
  if (!storage) return [];
  const raw = storage.getItem(RECENT_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (item): item is DraftSummary =>
        !!item &&
        typeof item === "object" &&
        typeof (item as DraftSummary).id === "string" &&
        typeof (item as DraftSummary).title === "string" &&
        typeof (item as DraftSummary).updatedAt === "string",
    );
  } catch {
    return [];
  }
}

function writeRecentDrafts(items: DraftSummary[]): void {
  const storage = safeLocalStorage();
  if (!storage) return;
  storage.setItem(RECENT_KEY, JSON.stringify(items.slice(0, MAX_RECENT)));
}

export function upsertRecentDraft(summary: DraftSummary): DraftSummary[] {
  const next = [summary, ...getRecentDrafts().filter((d) => d.id !== summary.id)];
  writeRecentDrafts(next);
  return next.slice(0, MAX_RECENT);
}

export function removeRecentDraft(id: string): DraftSummary[] {
  const next = getRecentDrafts().filter((d) => d.id !== id);
  writeRecentDrafts(next);
  return next;
}

export function getCurrentDraftId(): string | null {
  const storage = safeLocalStorage();
  if (!storage) return null;
  return storage.getItem(CURRENT_KEY);
}

export function setCurrentDraftId(id: string | null): void {
  const storage = safeLocalStorage();
  if (!storage) return;
  if (id === null) {
    storage.removeItem(CURRENT_KEY);
  } else {
    storage.setItem(CURRENT_KEY, id);
  }
}

export const RECENT_DRAFTS_LIMIT = MAX_RECENT;
