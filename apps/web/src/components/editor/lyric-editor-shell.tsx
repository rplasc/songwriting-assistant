"use client";

import { useCallback, useEffect, useRef, useSyncExternalStore } from "react";
import { useEditorAnalysis } from "@/features/analysis/use-editor-analysis";
import {
  DEFAULT_RHYME_MODE,
  readStoredRhymeMode,
  subscribeToRhymeMode,
  writeStoredRhymeMode,
  type ClientRhymeMode,
} from "@/features/analysis/rhyme-modes";
import { useDraftSaving } from "@/features/drafts/use-draft-saving";
import { useDraftLanguage } from "@/features/language/use-draft-language";
import type { Language } from "@/features/language/language-types";
import { useLyricEditor } from "@/features/editor/tiptap/use-lyric-editor";
import { EditorHeader } from "./editor-header";
import { EditorLayout } from "./editor-layout";
import { LyricEditor } from "./lyric-editor";
import { RhymePanel } from "./rhyme-panel";
import { SyllablePanel } from "./syllable-panel";

const getServerRhymeMode = () => DEFAULT_RHYME_MODE;

export function LyricEditorShell() {
  const { editor, activeLine } = useLyricEditor();

  const rhymeMode = useSyncExternalStore(
    subscribeToRhymeMode,
    readStoredRhymeMode,
    getServerRhymeMode,
  );

  const handleRhymeModeChange = useCallback((next: ClientRhymeMode) => {
    writeStoredRhymeMode(next);
  }, []);

  const { language, setLanguage } = useDraftLanguage();

  const { result, status, error } = useEditorAnalysis(
    activeLine,
    rhymeMode,
    language,
  );
  const {
    status: saveStatus,
    lastSavedAt,
    currentDraftId,
    recentDrafts,
    saveNow,
    loadDraft,
    newDraft,
  } = useDraftSaving(editor, {
    language,
    onDraftLoaded: (draft) => setLanguage(draft.language),
  });

  // Persist a language switch immediately if there's an existing draft —
  // otherwise the change would only land on the next keystroke.
  const saveNowRef = useRef(saveNow);
  useEffect(() => {
    saveNowRef.current = saveNow;
  }, [saveNow]);

  const handleLanguageChange = useCallback(
    (next: Language) => {
      if (next === language) return;
      setLanguage(next);
      if (currentDraftId && (editor?.getText().trim().length ?? 0) > 0) {
        queueMicrotask(() => void saveNowRef.current());
      }
    },
    [language, setLanguage, currentDraftId, editor],
  );

  return (
    <div className="flex flex-col gap-3">
      <EditorHeader
        rhymeMode={rhymeMode}
        onRhymeModeChange={handleRhymeModeChange}
        language={language}
        onLanguageChange={handleLanguageChange}
        saveStatus={saveStatus}
        lastSavedAt={lastSavedAt}
        onSave={() => void saveNow()}
        drafts={recentDrafts}
        currentDraftId={currentDraftId}
        onSelectDraft={(id) => void loadDraft(id)}
        onNewDraft={newDraft}
      />
      <EditorLayout
        editor={<LyricEditor editor={editor} />}
        panels={
          <>
            <SyllablePanel
              status={status}
              result={result}
              language={language}
            />
            <RhymePanel
              status={status}
              result={result}
              rhymeMode={rhymeMode}
              language={language}
              onRequestModeChange={handleRhymeModeChange}
            />
          </>
        }
      />
      {status === "error" && error ? (
        <div
          role="alert"
          className="mt-1 rounded border border-border bg-surface-muted px-3 py-2 text-[11px] text-muted-foreground"
        >
          {error} Keep writing — I&rsquo;ll catch up when I&rsquo;m back.
        </div>
      ) : null}
    </div>
  );
}
