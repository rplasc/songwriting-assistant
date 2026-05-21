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
import { jumpToLine } from "@/features/editor/tiptap/jump-to-line";
import { useDraftSections } from "@/features/structure/use-draft-sections";
import { useDraftAnalysis } from "@/features/draft-analysis/use-draft-analysis";
import { EditorHeader } from "./editor-header";
import { EditorLayout } from "./editor-layout";
import { LyricEditor } from "./lyric-editor";
import { RhymePanel } from "./rhyme-panel";
import { SyllablePanel } from "./syllable-panel";
import { DraftAnalysisRail } from "./draft-analysis-rail";

const getServerRhymeMode = () => DEFAULT_RHYME_MODE;

export function LyricEditorShell() {
  const { editor, activeLine, content } = useLyricEditor();

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
    stanzas,
    sections,
    labelFor,
    assignLabel,
    clearLabel,
    resetFromDraft,
  } = useDraftSections(editor);

  const {
    status: saveStatus,
    lastSavedAt,
    currentDraftId,
    recentDrafts,
    saveNow,
    loadDraft,
    newDraft,
    deleteDraft,
  } = useDraftSaving(editor, {
    language,
    sections,
    onDraftLoaded: (draft) => {
      setLanguage(draft.language);
      resetFromDraft(draft.sections);
    },
  });

  const {
    status: analysisStatus,
    analysis,
    error: analysisError,
    refresh: refreshAnalysis,
  } = useDraftAnalysis({
    draftId: currentDraftId,
    content,
    language,
    sections,
  });

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

  const handleAssignLabel = useCallback(
    (range: { lineStart: number; lineEnd: number }, label: string) => {
      assignLabel(range, label);
      if (currentDraftId) {
        queueMicrotask(() => void saveNowRef.current());
      }
    },
    [assignLabel, currentDraftId],
  );

  const handleClearLabel = useCallback(
    (range: { lineStart: number; lineEnd: number }) => {
      clearLabel(range);
      if (currentDraftId) {
        queueMicrotask(() => void saveNowRef.current());
      }
    },
    [clearLabel, currentDraftId],
  );

  const handleJump = useCallback(
    (lineStart: number) => {
      if (editor) jumpToLine(editor, lineStart);
    },
    [editor],
  );

  return (
    <div className="flex flex-col gap-4">
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
        onDeleteDraft={(id) => void deleteDraft(id)}
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
        rail={
          <DraftAnalysisRail
            status={analysisStatus}
            analysis={analysis}
            error={analysisError}
            language={language}
            stanzas={stanzas}
            labelFor={labelFor}
            onAssignLabel={handleAssignLabel}
            onClearLabel={handleClearLabel}
            onRefresh={() => void refreshAnalysis()}
            onJump={handleJump}
          />
        }
      />
      {status === "error" && error ? (
        <p role="alert" className="text-[11px] text-muted-foreground">
          {error} Keep writing — I&rsquo;ll catch up when I&rsquo;m back.
        </p>
      ) : null}
    </div>
  );
}
