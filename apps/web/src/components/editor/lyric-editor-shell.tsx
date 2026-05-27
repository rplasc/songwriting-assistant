"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
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
import { useDraftCompare } from "@/features/draft-compare/use-draft-compare";
import { EditorHeader } from "./editor-header";
import { EditorLayout } from "./editor-layout";
import { LyricEditor } from "./lyric-editor";
import { RhymePanel } from "./rhyme-panel";
import { SyllablePanel } from "./syllable-panel";
import { AdvancedRhymeExplorer } from "./advanced-rhyme-explorer";
import { DraftAnalysisRail } from "./draft-analysis-rail";
import { EditorNotice, NoticeAction } from "./editor-notice";

const getServerRhymeMode = () => DEFAULT_RHYME_MODE;

// Mirror the server-side DTO cap from apps/gateway/.../create-draft.dto.ts.
// When the text content nears this ceiling, surface a soft pre-flight notice.
const CONTENT_CEILING = 10_000;
const CONTENT_WARN_AT = Math.floor(CONTENT_CEILING * 0.9);

export function LyricEditorShell() {
  const { editor, activeLine, content } = useLyricEditor();
  const [explorerOpen, setExplorerOpen] = useState(false);

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
    droppedLabelCount,
    acknowledgeDroppedLabels,
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

  // Baseline is a stored revision hash; the gateway's SnapshotStore retains
  // the analysis payload behind that hash for the comparison call. Tag the
  // saved hash with its draftId so a draft switch implicitly invalidates the
  // baseline without needing an effect (snapshot hashes are draft-scoped on
  // the gateway).
  const [baseline, setBaseline] = useState<{
    draftId: string;
    revisionHash: string;
  } | null>(null);
  const baselineRevisionHash =
    baseline && baseline.draftId === currentDraftId
      ? baseline.revisionHash
      : null;
  const currentRevisionHash = analysis?.revisionHash ?? null;
  const baselineSet = baselineRevisionHash !== null;
  const baselineMatchesCurrent =
    baselineSet && baselineRevisionHash === currentRevisionHash;

  const {
    status: compareStatus,
    result: compareResult,
    error: compareError,
    run: runCompare,
    reset: resetCompare,
  } = useDraftCompare({
    draftId: currentDraftId,
    baseRevisionHash: baselineRevisionHash,
    targetRevisionHash: currentRevisionHash,
    language,
  });

  // If the user switches drafts, drop any compare result associated with the
  // old draft. The baseline itself stays tagged with its draftId so it's
  // naturally inert once the draft no longer matches. React state-during-
  // render handles draft switch without an effect's commit-phase delay.
  const [trackedDraftId, setTrackedDraftId] = useState(currentDraftId);
  if (trackedDraftId !== currentDraftId) {
    setTrackedDraftId(currentDraftId);
    resetCompare();
  }

  const handleSetBaseline = useCallback(() => {
    if (currentDraftId && currentRevisionHash) {
      setBaseline({
        draftId: currentDraftId,
        revisionHash: currentRevisionHash,
      });
    }
  }, [currentDraftId, currentRevisionHash]);

  const handleClearBaseline = useCallback(() => {
    setBaseline(null);
    resetCompare();
  }, [resetCompare]);

  const handleCompare = useCallback(() => {
    void runCompare();
  }, [runCompare]);

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

  // `content` is the editor's plain text; sized-against-the-DTO check is
  // intentionally soft — text underestimates the HTML payload, so a notice
  // near 90% of the ceiling is a comfortable early warning.
  const contentLength = useMemo(() => content.length, [content]);
  const nearCeiling = contentLength >= CONTENT_WARN_AT;

  const handleReload = useCallback(() => {
    if (currentDraftId) void loadDraft(currentDraftId);
  }, [currentDraftId, loadDraft]);

  const handleRetry = useCallback(() => {
    void saveNow();
  }, [saveNow]);

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
      {(saveStatus === "conflict" ||
        saveStatus === "error" ||
        droppedLabelCount > 0 ||
        nearCeiling) && (
        <div className="flex flex-col gap-1.5">
          {saveStatus === "conflict" && (
            <EditorNotice
              tone="alert"
              lead="This draft drifted."
              actions={
                currentDraftId ? (
                  <NoticeAction onClick={handleReload}>Reload</NoticeAction>
                ) : null
              }
            >
              Looks like the page changed in another window. Reload to see
              what&rsquo;s there.
            </EditorNotice>
          )}
          {saveStatus === "error" && (
            <EditorNotice
              tone="alert"
              lead="Save didn&rsquo;t take."
              actions={<NoticeAction onClick={handleRetry}>Try again</NoticeAction>}
            >
              The last few keystrokes didn&rsquo;t reach the page.
            </EditorNotice>
          )}
          {droppedLabelCount > 0 && (
            <EditorNotice
              tone="warn"
              lead={`${droppedLabelCount} label${droppedLabelCount === 1 ? "" : "s"} lost ${droppedLabelCount === 1 ? "its" : "their"} stanza.`}
              actions={
                <NoticeAction
                  emphasis="subtle"
                  onClick={acknowledgeDroppedLabels}
                >
                  Dismiss
                </NoticeAction>
              }
            >
              Pin them again from the gutter when the lines settle.
            </EditorNotice>
          )}
          {nearCeiling && (
            <EditorNotice tone="warn" lead="Getting full.">
              <span className="tabular-nums">
                {contentLength.toLocaleString()}
              </span>{" "}
              of{" "}
              <span className="tabular-nums">
                {CONTENT_CEILING.toLocaleString()}
              </span>{" "}
              characters in — consider tightening.
            </EditorNotice>
          )}
        </div>
      )}
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
              onOpenExplorer={() => setExplorerOpen(true)}
              explorerOpen={explorerOpen}
            />
            {explorerOpen && (
              <AdvancedRhymeExplorer
                activeLine={activeLine}
                language={language}
                enabled={explorerOpen}
                onClose={() => setExplorerOpen(false)}
              />
            )}
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
            compareStatus={compareStatus}
            compareResult={compareResult}
            compareError={compareError}
            baselineSet={baselineSet}
            baselineMatchesCurrent={baselineMatchesCurrent}
            onSetBaseline={handleSetBaseline}
            onClearBaseline={handleClearBaseline}
            onCompare={handleCompare}
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
