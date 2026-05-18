"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Editor } from "@tiptap/react";
import {
  createDraft,
  getDraft,
  updateDraft,
  DraftRequestError,
} from "./drafts-client";
import {
  getRecentDrafts,
  upsertRecentDraft,
  setCurrentDraftId as persistCurrentId,
  getCurrentDraftId as readCurrentId,
} from "./drafts-local-index";
import type { Draft, DraftSummary, SaveStatus } from "./drafts-types";

const AUTOSAVE_DEBOUNCE_MS = 1500;
const DEFAULT_TITLE = "Untitled Draft";

export interface UseDraftSavingReturn {
  status: SaveStatus;
  lastSavedAt: Date | null;
  currentDraftId: string | null;
  recentDrafts: DraftSummary[];
  saveNow: () => Promise<void>;
  loadDraft: (id: string) => Promise<void>;
  newDraft: () => void;
}

function deriveTitle(content: string): string {
  const firstLine = content
    .split(/\r?\n/)
    .map((l) => l.trim())
    .find((l) => l.length > 0);
  if (!firstLine) return DEFAULT_TITLE;
  return firstLine.length > 60 ? `${firstLine.slice(0, 57)}…` : firstLine;
}

function summarize(draft: Draft): DraftSummary {
  return {
    id: draft.id,
    title: draft.title || DEFAULT_TITLE,
    updatedAt: draft.updatedAt,
  };
}

export function useDraftSaving(
  editor: Editor | null,
): UseDraftSavingReturn {
  // Lazy initializers read localStorage once during the first render. Because
  // the parent is a "use client" component, this only runs in the browser.
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [currentDraftId, setCurrentDraftIdState] = useState<string | null>(() =>
    readCurrentId(),
  );
  const [recentDrafts, setRecentDrafts] = useState<DraftSummary[]>(() =>
    getRecentDrafts(),
  );

  // Refs for closure-free access from event handlers.
  const currentIdRef = useRef<string | null>(currentDraftId);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inFlightRef = useRef<AbortController | null>(null);
  const suppressDirtyRef = useRef(false);

  const updateCurrentId = useCallback((id: string | null) => {
    currentIdRef.current = id;
    setCurrentDraftIdState(id);
    persistCurrentId(id);
  }, []);

  const flushSave = useCallback(async () => {
    if (!editor) return;
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }
    if (inFlightRef.current) {
      inFlightRef.current.abort();
    }
    const controller = new AbortController();
    inFlightRef.current = controller;

    const content = editor.getText();
    if (content.trim().length === 0) {
      // Nothing meaningful to save yet — keep status idle.
      setStatus("idle");
      return;
    }

    setStatus("saving");
    try {
      let saved: Draft;
      if (currentIdRef.current) {
        saved = await updateDraft(
          currentIdRef.current,
          { content },
          { signal: controller.signal },
        );
      } else {
        saved = await createDraft(
          { content, title: deriveTitle(content) },
          { signal: controller.signal },
        );
        updateCurrentId(saved.id);
      }
      setLastSavedAt(new Date(saved.updatedAt));
      setStatus("saved");
      setRecentDrafts(upsertRecentDraft(summarize(saved)));
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      if (err instanceof DraftRequestError && err.status === 404) {
        // Draft id is stale — clear it and let the next save create fresh.
        updateCurrentId(null);
      }
      setStatus("offline");
    } finally {
      if (inFlightRef.current === controller) {
        inFlightRef.current = null;
      }
    }
  }, [editor, updateCurrentId]);

  const saveNow = useCallback(async () => {
    await flushSave();
  }, [flushSave]);

  // Mark dirty + schedule autosave on every editor update.
  useEffect(() => {
    if (!editor) return;
    const handleUpdate = () => {
      if (suppressDirtyRef.current) return;
      const content = editor.getText();
      if (content.trim().length === 0) {
        // Empty editor stays idle so we don't autosave an empty draft.
        if (debounceRef.current) {
          clearTimeout(debounceRef.current);
          debounceRef.current = null;
        }
        setStatus("idle");
        return;
      }
      setStatus("dirty");
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        debounceRef.current = null;
        void flushSave();
      }, AUTOSAVE_DEBOUNCE_MS);
    };
    editor.on("update", handleUpdate);
    return () => {
      editor.off("update", handleUpdate);
    };
  }, [editor, flushSave]);

  // Cancel any pending work on unmount.
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      if (inFlightRef.current) inFlightRef.current.abort();
    };
  }, []);

  const loadDraft = useCallback(
    async (id: string) => {
      if (!editor) return;
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
        debounceRef.current = null;
      }
      if (inFlightRef.current) inFlightRef.current.abort();
      const controller = new AbortController();
      inFlightRef.current = controller;

      setStatus("saving");
      try {
        const draft = await getDraft(id, { signal: controller.signal });
        suppressDirtyRef.current = true;
        editor.commands.setContent(draft.content || "");
        suppressDirtyRef.current = false;
        updateCurrentId(draft.id);
        setLastSavedAt(new Date(draft.updatedAt));
        setStatus("saved");
        setRecentDrafts(upsertRecentDraft(summarize(draft)));
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
        setStatus("offline");
      } finally {
        if (inFlightRef.current === controller) {
          inFlightRef.current = null;
        }
      }
    },
    [editor, updateCurrentId],
  );

  const newDraft = useCallback(() => {
    if (!editor) return;
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }
    if (inFlightRef.current) inFlightRef.current.abort();
    suppressDirtyRef.current = true;
    editor.commands.setContent("");
    suppressDirtyRef.current = false;
    updateCurrentId(null);
    setLastSavedAt(null);
    setStatus("idle");
  }, [editor, updateCurrentId]);

  return {
    status,
    lastSavedAt,
    currentDraftId,
    recentDrafts,
    saveNow,
    loadDraft,
    newDraft,
  };
}
