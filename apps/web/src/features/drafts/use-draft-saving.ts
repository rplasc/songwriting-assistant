"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Editor } from "@tiptap/react";
import type { Language } from "@/features/language/language-types";
import {
  createDraft,
  deleteDraft as deleteDraftRequest,
  getDraft,
  updateDraft,
  DraftRequestError,
} from "./drafts-client";
import {
  getRecentDrafts,
  removeRecentDraft,
  upsertRecentDraft,
  setCurrentDraftId as persistCurrentId,
  getCurrentDraftId as readCurrentId,
} from "./drafts-local-index";
import type { Draft, DraftSummary, SaveStatus } from "./drafts-types";
import { deriveTitle, DEFAULT_TITLE } from "./derive-title";
import { getEditorText } from "@/features/editor/tiptap/editor-lines";

const AUTOSAVE_DEBOUNCE_MS = 1500;

// Bounded retry budget for network-class failures. The client stays in
// "offline" between attempts and transitions to "error" after exhausting
// the budget. Conflicts and validation errors are terminal immediately.
const RETRY_DELAYS_MS = [1000, 3000, 8000];
const JITTER = 0.25;

function parseStoredContent(raw: string): string {
  if (!raw) return "<p></p>";
  // New format: HTML saved by editor.getHTML() — pass through directly.
  if (raw.trimStart().startsWith("<")) return raw;
  // Legacy format: plain text saved by editor.getText() with \n\n blockSeparator.
  return (
    raw
      .split(/\r?\n\r?\n/)
      .map((para) => {
        const escaped = para
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;");
        return `<p>${escaped}</p>`;
      })
      .join("") || "<p></p>"
  );
}

export interface UseDraftSavingOptions {
  language: Language;
  /**
   * Returns the manually-set title, or null when the title should derive
   * from the first lyric line. Read at save time (a ref-backed getter keeps
   * a just-committed title from being missed by effect timing).
   */
  getTitle?: () => string | null;
  onDraftLoaded?: (draft: Draft) => void;
}

export interface UseDraftSavingReturn {
  status: SaveStatus;
  lastSavedAt: Date | null;
  currentDraftId: string | null;
  currentDraftLanguage: Language | null;
  recentDrafts: DraftSummary[];
  saveNow: () => Promise<void>;
  loadDraft: (id: string) => Promise<void>;
  newDraft: () => void;
  deleteDraft: (id: string) => Promise<void>;
}

function summarize(draft: Draft): DraftSummary {
  return {
    id: draft.id,
    title: draft.title || DEFAULT_TITLE,
    language: draft.language,
    updatedAt: draft.updatedAt,
  };
}

function isAbortError(err: unknown): boolean {
  return (err as Error)?.name === "AbortError";
}

function isRetryable(err: unknown): boolean {
  if (err instanceof DraftRequestError) {
    // 4xx are terminal (validation, conflict, not found, etc.). 5xx are
    // worth retrying — the server may recover.
    return err.status !== undefined && err.status >= 500;
  }
  // Native fetch failures throw TypeError on network errors.
  return err instanceof TypeError;
}

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException("Aborted", "AbortError"));
      return;
    }
    const t = setTimeout(() => {
      signal.removeEventListener("abort", onAbort);
      resolve();
    }, ms);
    const onAbort = () => {
      clearTimeout(t);
      reject(new DOMException("Aborted", "AbortError"));
    };
    signal.addEventListener("abort", onAbort, { once: true });
  });
}

export function useDraftSaving(
  editor: Editor | null,
  { language, getTitle, onDraftLoaded }: UseDraftSavingOptions,
): UseDraftSavingReturn {
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [currentDraftId, setCurrentDraftIdState] = useState<string | null>(() =>
    readCurrentId(),
  );
  const [currentDraftLanguage, setCurrentDraftLanguage] =
    useState<Language | null>(null);
  const [recentDrafts, setRecentDrafts] = useState<DraftSummary[]>(() =>
    getRecentDrafts(),
  );

  const currentIdRef = useRef<string | null>(currentDraftId);
  const currentDraftLanguageRef = useRef<Language | null>(null);
  const currentVersionRef = useRef<number | null>(null);
  const languageRef = useRef<Language>(language);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inFlightRef = useRef<AbortController | null>(null);
  const suppressDirtyRef = useRef(false);
  const onDraftLoadedRef = useRef(onDraftLoaded);
  const getTitleRef = useRef(getTitle);

  useEffect(() => {
    onDraftLoadedRef.current = onDraftLoaded;
    getTitleRef.current = getTitle;
  }, [onDraftLoaded, getTitle]);

  const updateCurrentId = useCallback((id: string | null) => {
    currentIdRef.current = id;
    setCurrentDraftIdState(id);
    persistCurrentId(id);
  }, []);

  const updateCurrentLanguage = useCallback((lang: Language | null) => {
    currentDraftLanguageRef.current = lang;
    setCurrentDraftLanguage(lang);
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

    if (editor.state.doc.textContent.trim().length === 0) {
      setStatus("idle");
      return;
    }

    const content = editor.getHTML();
    const text = getEditorText(editor);
    // A manually-set title wins; otherwise the title tracks the first lyric
    // line so the drafts picker never shows a stale name.
    const title = getTitleRef.current?.() ?? deriveTitle(text);

    setStatus("saving");
    const targetLanguage = languageRef.current;

    const attemptSave = async (): Promise<Draft> => {
      if (currentIdRef.current) {
        const patch: {
          content: string;
          title: string;
          language?: Language;
          expectedVersion?: number;
        } = { content, title };
        if (
          currentDraftLanguageRef.current &&
          currentDraftLanguageRef.current !== targetLanguage
        ) {
          patch.language = targetLanguage;
        }
        if (currentVersionRef.current !== null) {
          patch.expectedVersion = currentVersionRef.current;
        }
        return updateDraft(currentIdRef.current, patch, {
          signal: controller.signal,
        });
      }
      const created = await createDraft(
        {
          content,
          title,
          language: targetLanguage,
        },
        { signal: controller.signal },
      );
      updateCurrentId(created.id);
      return created;
    };

    let attempt = 0;
    while (true) {
      try {
        const saved = await attemptSave();
        currentVersionRef.current = saved.version;
        updateCurrentLanguage(saved.language);
        setLastSavedAt(new Date(saved.updatedAt));
        setStatus("saved");
        setRecentDrafts(upsertRecentDraft(summarize(saved)));
        return;
      } catch (err) {
        if (isAbortError(err)) return;
        if (err instanceof DraftRequestError) {
          if (err.status === 409) {
            // Another writer advanced the draft. Don't retry, don't clobber
            // — surface the conflict and let the user decide (reload).
            setStatus("conflict");
            return;
          }
          if (err.status === 404) {
            // Server-side draft is gone. Reset local pointer so the next
            // save creates a fresh one instead of looping on a dead id.
            updateCurrentId(null);
            updateCurrentLanguage(null);
            currentVersionRef.current = null;
            setStatus("error");
            return;
          }
        }
        if (!isRetryable(err) || attempt >= RETRY_DELAYS_MS.length) {
          setStatus("error");
          return;
        }
        setStatus("offline");
        const base = RETRY_DELAYS_MS[attempt];
        const jitter = base * JITTER * (Math.random() * 2 - 1);
        try {
          await sleep(Math.max(0, base + jitter), controller.signal);
        } catch {
          return; // aborted during backoff
        }
        attempt += 1;
      }
    }
  }, [editor, updateCurrentId, updateCurrentLanguage]);

  // Track the running flush so the unmount/abort path can clear it.
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      if (inFlightRef.current) inFlightRef.current.abort();
    };
  }, []);

  const saveNow = useCallback(async () => {
    await flushSave();
  }, [flushSave]);

  useEffect(() => {
    languageRef.current = language;
  }, [language]);

  useEffect(() => {
    if (!editor) return;
    const handleUpdate = () => {
      if (suppressDirtyRef.current) return;
      if (editor.state.doc.textContent.trim().length === 0) {
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
        editor.commands.setContent(parseStoredContent(draft.content), true);
        suppressDirtyRef.current = false;
        updateCurrentId(draft.id);
        updateCurrentLanguage(draft.language);
        currentVersionRef.current = draft.version;
        setLastSavedAt(new Date(draft.updatedAt));
        setStatus("saved");
        setRecentDrafts(upsertRecentDraft(summarize(draft)));
        onDraftLoadedRef.current?.(draft);
      } catch (err) {
        if (isAbortError(err)) return;
        if (err instanceof DraftRequestError && err.status === 404) {
          setRecentDrafts(removeRecentDraft(id));
          setStatus("idle");
        } else {
          setStatus("offline");
        }
      } finally {
        if (inFlightRef.current === controller) {
          inFlightRef.current = null;
        }
      }
    },
    [editor, updateCurrentId, updateCurrentLanguage],
  );

  const deleteDraft = useCallback(
    async (id: string) => {
      const isCurrent = currentIdRef.current === id;
      // Optimistically remove from the local index so the picker updates
      // immediately — the network call is the source of truth but the UI
      // shouldn't wait on it.
      setRecentDrafts(removeRecentDraft(id));
      if (isCurrent && editor) {
        if (debounceRef.current) {
          clearTimeout(debounceRef.current);
          debounceRef.current = null;
        }
        if (inFlightRef.current) inFlightRef.current.abort();
        suppressDirtyRef.current = true;
        editor.commands.setContent("", true);
        suppressDirtyRef.current = false;
        updateCurrentId(null);
        updateCurrentLanguage(null);
        currentVersionRef.current = null;
        setLastSavedAt(null);
        setStatus("idle");
      }
      try {
        await deleteDraftRequest(id);
      } catch (err) {
        if (err instanceof DraftRequestError && err.status === 404) return;
        // Re-surface other failures via the offline indicator so the user
        // knows the server copy may still exist.
        setStatus("offline");
      }
    },
    [editor, updateCurrentId, updateCurrentLanguage],
  );

  const newDraft = useCallback(() => {
    if (!editor) return;
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }
    if (inFlightRef.current) inFlightRef.current.abort();
    suppressDirtyRef.current = true;
    editor.commands.setContent("", true);
    suppressDirtyRef.current = false;
    updateCurrentId(null);
    updateCurrentLanguage(null);
    currentVersionRef.current = null;
    setLastSavedAt(null);
    setStatus("idle");
  }, [editor, updateCurrentId, updateCurrentLanguage]);

  return {
    status,
    lastSavedAt,
    currentDraftId,
    currentDraftLanguage,
    recentDrafts,
    saveNow,
    loadDraft,
    newDraft,
    deleteDraft,
  };
}
