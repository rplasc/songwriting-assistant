"use client";

import { useCallback, useSyncExternalStore } from "react";
import { useEditorAnalysis } from "@/features/analysis/use-editor-analysis";
import {
  DEFAULT_RHYME_MODE,
  readStoredRhymeMode,
  subscribeToRhymeMode,
  writeStoredRhymeMode,
  type RhymeMode,
} from "@/features/analysis/rhyme-modes";
import { useDraftSaving } from "@/features/drafts/use-draft-saving";
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

  const handleRhymeModeChange = useCallback((next: RhymeMode) => {
    writeStoredRhymeMode(next);
  }, []);

  const { result, status, error } = useEditorAnalysis(activeLine, rhymeMode);
  const {
    status: saveStatus,
    lastSavedAt,
    currentDraftId,
    recentDrafts,
    saveNow,
    loadDraft,
    newDraft,
  } = useDraftSaving(editor);

  return (
    <div className="flex flex-col gap-3">
      <EditorHeader
        rhymeMode={rhymeMode}
        onRhymeModeChange={handleRhymeModeChange}
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
            <SyllablePanel status={status} result={result} />
            <RhymePanel
              status={status}
              result={result}
              rhymeMode={rhymeMode}
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
          {error} Keep writing — analysis will retry automatically.
        </div>
      ) : null}
    </div>
  );
}
