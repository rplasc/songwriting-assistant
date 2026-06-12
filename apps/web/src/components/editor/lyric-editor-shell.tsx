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
import { buildLineNotes } from "@/features/analysis/line-notes";
import { useLineSyllables } from "@/features/analysis/use-line-syllables";
import { useDraftSaving } from "@/features/drafts/use-draft-saving";
import {
  DEFAULT_TITLE,
  deriveTitle,
  deriveTitleLine,
  truncateTitle,
} from "@/features/drafts/derive-title";
import { getEditorText } from "@/features/editor/tiptap/editor-lines";
import { useDraftLanguage } from "@/features/language/use-draft-language";
import type { Language } from "@/features/language/language-types";
import { usePreferences } from "@/features/settings/preferences";
import { useLyricEditor } from "@/features/editor/tiptap/use-lyric-editor";
import { jumpToLine } from "@/features/editor/tiptap/jump-to-line";
import { insertSectionLabel } from "@/features/editor/tiptap/insert-section-label";
import { PASTE_AS_LINES_META } from "@/features/editor/tiptap/paste-as-lines";
import { setInnerRhymes } from "@/features/editor/tiptap/inner-rhyme-extension";
import { useDraftAnalysis } from "@/features/draft-analysis/use-draft-analysis";
import { useDraftCompare } from "@/features/draft-compare/use-draft-compare";
import { NotebookHeader } from "./notebook-header";
import { NotebookLayout } from "./notebook-layout";
import { LyricEditor } from "./lyric-editor";
import { AdvancedRhymeExplorer } from "./advanced-rhyme-explorer";
import { MarginRail } from "./margin-rail";
import { RhymeSuggestionStrip } from "./rhyme-suggestion-strip";
import { EditorStatusStrip } from "./editor-status-strip";
import { EditorNotice, NoticeAction } from "./editor-notice";

const getServerRhymeMode = () => DEFAULT_RHYME_MODE;

// Mirror the server-side DTO cap from apps/gateway/.../create-draft.dto.ts.
// When the text content nears this ceiling, surface a soft pre-flight notice.
const CONTENT_CEILING = 10_000;
const CONTENT_WARN_AT = Math.floor(CONTENT_CEILING * 0.9);

const RAIL_STORAGE_KEY = "songwriting-assistant.margin-rail.collapsed";

export function LyricEditorShell() {
  const { editor, activeLine, activeWord, activeLineNumber, content } =
    useLyricEditor();
  const [explorerOpen, setExplorerOpen] = useState(false);

  // Rail visibility — read the persisted preference after mount to avoid a
  // server/client hydration mismatch, then persist on change.
  const [railOpen, setRailOpen] = useState(true);
  const isFirstRailRender = useRef(true);
  useEffect(() => {
    try {
      if (window.localStorage.getItem(RAIL_STORAGE_KEY) === "1") {
        // eslint-disable-next-line react-hooks/set-state-in-effect -- seeding from localStorage post-mount to avoid a hydration mismatch
        setRailOpen(false);
      }
    } catch {
      // localStorage unavailable — ignore.
    }
  }, []);
  useEffect(() => {
    if (isFirstRailRender.current) {
      isFirstRailRender.current = false;
      return;
    }
    try {
      window.localStorage.setItem(RAIL_STORAGE_KEY, railOpen ? "0" : "1");
    } catch {
      // localStorage unavailable — ignore.
    }
  }, [railOpen]);

  const rhymeMode = useSyncExternalStore(
    subscribeToRhymeMode,
    readStoredRhymeMode,
    getServerRhymeMode,
  );

  const handleRhymeModeChange = useCallback((next: ClientRhymeMode) => {
    writeStoredRhymeMode(next);
  }, []);

  const { language, setLanguage } = useDraftLanguage();

  // A manually-set title detaches from the editor: it no longer follows the
  // first lyric line and is never written into the editor text. Null means
  // "derive from the first lyric line" (the original behavior). The ref
  // mirrors the state so the save path reads a just-committed title without
  // waiting on a re-render.
  const [manualTitle, setManualTitleState] = useState<string | null>(null);
  const manualTitleRef = useRef<string | null>(null);
  const setManualTitle = useCallback((title: string | null) => {
    manualTitleRef.current = title;
    setManualTitleState(title);
  }, []);

  const {
    theme,
    rhymeHighlights,
    rhymeHighlightStyle,
    syllableCounts,
    setTheme,
    setRhymeHighlights,
    setRhymeHighlightStyle,
    setSyllableCounts,
  } = usePreferences();

  const { result, status } = useEditorAnalysis(
    activeLine,
    activeWord,
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
    deleteDraft,
  } = useDraftSaving(editor, {
    language,
    getTitle: () => manualTitleRef.current,
    onDraftLoaded: (draft) => {
      setLanguage(draft.language);
      // A stored title that doesn't match the first lyric line was set by
      // hand — keep it detached. Matching (or default) titles stay derived.
      const text = editor ? getEditorText(editor) : "";
      const detached =
        draft.title.trim().length > 0 &&
        draft.title !== deriveTitle(text) &&
        draft.title !== DEFAULT_TITLE;
      setManualTitle(detached ? draft.title : null);
    },
  });

  const {
    status: analysisStatus,
    analysis,
    analyzedContent,
    error: analysisError,
    refresh: refreshAnalysis,
    analyzeNow,
  } = useDraftAnalysis({
    draftId: currentDraftId,
    content,
    language,
  });

  // A multi-line paste fills lines the live caret analysis will never visit,
  // so analyze immediately instead of waiting out the stale-idle window —
  // that's what backfills the margin syllable counts for every pasted line.
  const [pasteTick, setPasteTick] = useState(0);
  useEffect(() => {
    if (!editor) return;
    const onTransaction = ({
      transaction,
    }: {
      transaction: { getMeta: (key: string) => unknown };
    }) => {
      if (transaction.getMeta(PASTE_AS_LINES_META)) {
        setPasteTick((t) => t + 1);
      }
    };
    editor.on("transaction", onTransaction);
    return () => {
      editor.off("transaction", onTransaction);
    };
  }, [editor]);
  useEffect(() => {
    // Runs after useDraftAnalysis has synced its content ref, so the
    // analysis sees the post-paste text.
    if (pasteTick > 0) void analyzeNow();
  }, [pasteTick, analyzeNow]);

  // ── Editor decorations ────────────────────────────────────────────────
  // Per-line syllable counts: draft analysis backfills every line, the live
  // WS result keeps the caret line instant.
  useLineSyllables({
    editor,
    analysis,
    analyzedContent,
    liveResult: result,
  });

  // Inner-rhyme underlines from the latest full-draft analysis. When the
  // writer turns highlights off, clear any existing underlines and hold.
  useEffect(() => {
    if (!editor) return;
    if (!rhymeHighlights) {
      setInnerRhymes(editor, { groups: [], sourceLines: [] });
      return;
    }
    if (!analysis || analyzedContent === null) return;
    setInnerRhymes(editor, {
      groups: analysis.innerRhymes,
      sourceLines: analyzedContent.split("\n"),
    });
  }, [editor, analysis, analyzedContent, rhymeHighlights]);

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

  const handleJump = useCallback(
    (lineStart: number) => {
      if (editor) jumpToLine(editor, lineStart);
    },
    [editor],
  );

  const handleInsertWord = useCallback(
    (word: string) => {
      if (!editor) return;
      const { $from } = editor.state.selection;
      const beforeCaret = $from.parent.textContent.slice(0, $from.parentOffset);
      const needsSpace = /\S$/.test(beforeCaret);
      editor
        .chain()
        .focus()
        .insertContent(needsSpace ? ` ${word}` : word)
        .run();
    },
    [editor],
  );

  const handleInsertSection = useCallback(
    (label: string) => {
      if (editor) insertSectionLabel(editor, label);
    },
    [editor],
  );

  // Committing a title detaches it from the editor text; committing an empty
  // title re-attaches (back to deriving from the first lyric line). Either
  // way the editor content is left alone, and the new title is persisted.
  const handleTitleChange = useCallback(
    (title: string) => {
      const trimmed = title.trim();
      setManualTitle(trimmed.length > 0 ? trimmed : null);
      if (currentDraftId && (editor?.getText().trim().length ?? 0) > 0) {
        queueMicrotask(() => void saveNowRef.current());
      }
    },
    [setManualTitle, currentDraftId, editor],
  );

  const lineNotes = useMemo(
    () =>
      buildLineNotes({
        result,
        analysis,
        activeLineNumber,
        language,
      }),
    [result, analysis, activeLineNumber, language],
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
    <div className="flex flex-col gap-5">
      <NotebookHeader
        displayTitle={
          manualTitle !== null ? truncateTitle(manualTitle) : deriveTitle(content)
        }
        editableTitle={manualTitle ?? deriveTitleLine(content)}
        onTitleChange={handleTitleChange}
        rhymeMode={rhymeMode}
        onRhymeModeChange={handleRhymeModeChange}
        language={language}
        onLanguageChange={handleLanguageChange}
        saveStatus={saveStatus}
        lastSavedAt={lastSavedAt}
        drafts={recentDrafts}
        currentDraftId={currentDraftId}
        onSelectDraft={(id) => void loadDraft(id)}
        onNewDraft={() => {
          setManualTitle(null);
          newDraft();
        }}
        onDeleteDraft={(id) => {
          if (id === currentDraftId) setManualTitle(null);
          void deleteDraft(id);
        }}
        theme={theme}
        onThemeChange={setTheme}
        rhymeHighlights={rhymeHighlights}
        onRhymeHighlightsChange={setRhymeHighlights}
        rhymeHighlightStyle={rhymeHighlightStyle}
        onRhymeHighlightStyleChange={setRhymeHighlightStyle}
        syllableCounts={syllableCounts}
        onSyllableCountsChange={setSyllableCounts}
      />
      {(saveStatus === "conflict" ||
        saveStatus === "error" ||
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
      <NotebookLayout
        railOpen={railOpen}
        main={
          <>
            <LyricEditor
              editor={editor}
              rhymeHighlightStyle={rhymeHighlightStyle}
              syllableCounts={syllableCounts}
            />
            {explorerOpen && (
              <AdvancedRhymeExplorer
                activeLine={activeLine}
                activeWord={activeWord}
                language={language}
                enabled={explorerOpen}
                onClose={() => setExplorerOpen(false)}
              />
            )}
            <RhymeSuggestionStrip
              status={status}
              result={result}
              rhymeMode={rhymeMode}
              language={language}
              onRequestModeChange={handleRhymeModeChange}
              onInsertWord={handleInsertWord}
              onOpenExplorer={() => setExplorerOpen(true)}
              explorerOpen={explorerOpen}
            />
            <EditorStatusStrip
              railOpen={railOpen}
              rhymeGroupCount={analysis?.innerRhymes.length ?? 0}
              rhymeHighlights={rhymeHighlights}
              rhymeHighlightStyle={rhymeHighlightStyle}
              syllableCounts={syllableCounts}
              offline={status === "error"}
              language={language}
            />
          </>
        }
        rail={
          <MarginRail
            open={railOpen}
            onToggle={() => setRailOpen((v) => !v)}
            language={language}
            lineStatus={status}
            lineResult={result}
            lineNotes={lineNotes}
            status={analysisStatus}
            analysis={analysis}
            error={analysisError}
            onRefresh={() => void refreshAnalysis()}
            onJump={handleJump}
            onInsertSection={handleInsertSection}
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
    </div>
  );
}
