"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Editor } from "@tiptap/react";
import type { Language } from "@/features/language/language-types";
import type { DraftSection } from "@/features/structure/structure-types";
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
import { getEditorText } from "@/features/editor/tiptap/editor-lines";

const AUTOSAVE_DEBOUNCE_MS = 1500;
const DEFAULT_TITLE = "Untitled Draft";

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
  sections?: DraftSection[];
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
    language: draft.language,
    updatedAt: draft.updatedAt,
  };
}

export function useDraftSaving(
  editor: Editor | null,
  { language, sections, onDraftLoaded }: UseDraftSavingOptions,
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
  const languageRef = useRef<Language>(language);
  const sectionsRef = useRef<DraftSection[]>(sections ?? []);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inFlightRef = useRef<AbortController | null>(null);
  const suppressDirtyRef = useRef(false);
  const onDraftLoadedRef = useRef(onDraftLoaded);

  useEffect(() => {
    onDraftLoadedRef.current = onDraftLoaded;
  }, [onDraftLoaded]);

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

    setStatus("saving");
    const targetLanguage = languageRef.current;
    try {
      let saved: Draft;
      if (currentIdRef.current) {
        const patch: {
          content: string;
          language?: Language;
          sections?: DraftSection[];
        } = { content, sections: sectionsRef.current };
        if (
          currentDraftLanguageRef.current &&
          currentDraftLanguageRef.current !== targetLanguage
        ) {
          patch.language = targetLanguage;
        }
        saved = await updateDraft(currentIdRef.current, patch, {
          signal: controller.signal,
        });
      } else {
        saved = await createDraft(
          {
            content,
            title: deriveTitle(text),
            language: targetLanguage,
            sections: sectionsRef.current,
          },
          { signal: controller.signal },
        );
        updateCurrentId(saved.id);
      }
      updateCurrentLanguage(saved.language);
      setLastSavedAt(new Date(saved.updatedAt));
      setStatus("saved");
      setRecentDrafts(upsertRecentDraft(summarize(saved)));
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      if (err instanceof DraftRequestError && err.status === 404) {
        updateCurrentId(null);
        updateCurrentLanguage(null);
      }
      setStatus("offline");
    } finally {
      if (inFlightRef.current === controller) {
        inFlightRef.current = null;
      }
    }
  }, [editor, updateCurrentId, updateCurrentLanguage]);

  const saveNow = useCallback(async () => {
    await flushSave();
  }, [flushSave]);

  useEffect(() => {
    languageRef.current = language;
  }, [language]);

  useEffect(() => {
    sectionsRef.current = sections ?? [];
  }, [sections]);

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
        editor.commands.setContent(parseStoredContent(draft.content));
        suppressDirtyRef.current = false;
        updateCurrentId(draft.id);
        updateCurrentLanguage(draft.language);
        setLastSavedAt(new Date(draft.updatedAt));
        setStatus("saved");
        setRecentDrafts(upsertRecentDraft(summarize(draft)));
        onDraftLoadedRef.current?.(draft);
      } catch (err) {
        if ((err as Error).name === "AbortError") return;
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
        editor.commands.setContent("");
        suppressDirtyRef.current = false;
        updateCurrentId(null);
        updateCurrentLanguage(null);
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
    editor.commands.setContent("");
    suppressDirtyRef.current = false;
    updateCurrentId(null);
    updateCurrentLanguage(null);
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
