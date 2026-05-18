import { beforeEach, describe, expect, it } from "vitest";
import {
  getCurrentDraftId,
  getRecentDrafts,
  RECENT_DRAFTS_LIMIT,
  removeRecentDraft,
  setCurrentDraftId,
  upsertRecentDraft,
} from "@/features/drafts/drafts-local-index";
import type { DraftSummary } from "@/features/drafts/drafts-types";

function makeSummary(id: string, title = `Draft ${id}`): DraftSummary {
  return { id, title, updatedAt: new Date().toISOString() };
}

describe("drafts-local-index", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("returns an empty list when nothing is stored", () => {
    expect(getRecentDrafts()).toEqual([]);
  });

  it("upserts a new summary to the front of the list", () => {
    upsertRecentDraft(makeSummary("a"));
    upsertRecentDraft(makeSummary("b"));
    const list = getRecentDrafts();
    expect(list.map((d) => d.id)).toEqual(["b", "a"]);
  });

  it("moves an existing summary to the front when re-saved", () => {
    upsertRecentDraft(makeSummary("a"));
    upsertRecentDraft(makeSummary("b"));
    upsertRecentDraft(makeSummary("a", "Draft a updated"));
    const list = getRecentDrafts();
    expect(list.map((d) => d.id)).toEqual(["a", "b"]);
    expect(list[0].title).toBe("Draft a updated");
  });

  it("caps the list at the documented limit", () => {
    for (let i = 0; i < RECENT_DRAFTS_LIMIT + 3; i += 1) {
      upsertRecentDraft(makeSummary(`d${i}`));
    }
    expect(getRecentDrafts()).toHaveLength(RECENT_DRAFTS_LIMIT);
  });

  it("removes a summary by id", () => {
    upsertRecentDraft(makeSummary("a"));
    upsertRecentDraft(makeSummary("b"));
    removeRecentDraft("a");
    expect(getRecentDrafts().map((d) => d.id)).toEqual(["b"]);
  });

  it("returns [] if the stored value is garbage", () => {
    window.localStorage.setItem("sa.drafts.recent", "{not-json");
    expect(getRecentDrafts()).toEqual([]);
  });

  it("tracks the current draft id", () => {
    expect(getCurrentDraftId()).toBeNull();
    setCurrentDraftId("abc");
    expect(getCurrentDraftId()).toBe("abc");
    setCurrentDraftId(null);
    expect(getCurrentDraftId()).toBeNull();
  });
});
