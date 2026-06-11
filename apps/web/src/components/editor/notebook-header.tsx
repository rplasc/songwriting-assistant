"use client";

import { useEffect, useRef, useState } from "react";
import type { ClientRhymeMode } from "@/features/analysis/rhyme-modes";
import type { DraftSummary, SaveStatus } from "@/features/drafts/drafts-types";
import type { Language } from "@/features/language/language-types";
import type {
  RhymeHighlightStyle,
  ThemePreference,
} from "@/features/settings/preferences";
import { DraftPicker } from "./draft-picker";
import { LanguageSelector } from "./language-selector";
import { RhymeModeToggle } from "./rhyme-mode-toggle";
import { SaveStatusIndicator } from "./save-status";
import { SettingsMenu } from "./settings-menu";

const SUBTITLE: Record<Language, string> = {
  en: "A lyric notebook. Write to see rhymes, get feedback, and keep track of your drafts.",
  es: "Un cuaderno de letras. Escribe para ver rimas, recibir comentarios y hacer un seguimiento de tus borradores.",
};

const TITLE_PLACEHOLDER: Record<Language, string> = {
  en: "Untitled draft",
  es: "Borrador sin título",
};

const EDIT_TITLE_LABEL: Record<Language, string> = {
  en: "Edit draft title",
  es: "Editar el título del borrador",
};

interface NotebookHeaderProps {
  /** Truncated, defaulted title for display. */
  displayTitle: string;
  /** Untruncated title text used as the input value while editing. */
  editableTitle: string;
  onTitleChange: (title: string) => void;
  rhymeMode: ClientRhymeMode;
  onRhymeModeChange: (mode: ClientRhymeMode) => void;
  language: Language;
  onLanguageChange: (lang: Language) => void;
  saveStatus: SaveStatus;
  lastSavedAt: Date | null;
  drafts: DraftSummary[];
  currentDraftId: string | null;
  onSelectDraft: (id: string) => void;
  onNewDraft: () => void;
  onDeleteDraft: (id: string) => void;
  theme: ThemePreference;
  onThemeChange: (theme: ThemePreference) => void;
  rhymeHighlights: boolean;
  onRhymeHighlightsChange: (on: boolean) => void;
  rhymeHighlightStyle: RhymeHighlightStyle;
  onRhymeHighlightStyleChange: (style: RhymeHighlightStyle) => void;
  syllableCounts: boolean;
  onSyllableCountsChange: (on: boolean) => void;
}

export function NotebookHeader({
  displayTitle,
  editableTitle,
  onTitleChange,
  rhymeMode,
  onRhymeModeChange,
  language,
  onLanguageChange,
  saveStatus,
  lastSavedAt,
  drafts,
  currentDraftId,
  onSelectDraft,
  onNewDraft,
  onDeleteDraft,
  theme,
  onThemeChange,
  rhymeHighlights,
  onRhymeHighlightsChange,
  rhymeHighlightStyle,
  onRhymeHighlightStyleChange,
  syllableCounts,
  onSyllableCountsChange,
}: NotebookHeaderProps) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-x-8 gap-y-4">
      <div className="min-w-0">
        <EditableTitle
          displayTitle={displayTitle}
          editableTitle={editableTitle}
          placeholder={TITLE_PLACEHOLDER[language]}
          editLabel={EDIT_TITLE_LABEL[language]}
          onCommit={onTitleChange}
        />
        <p className="mt-1 font-serif text-[13px] italic text-muted-foreground">
          {SUBTITLE[language]}
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-3.5">
        <LanguageSelector value={language} onChange={onLanguageChange} />
        <RhymeModeToggle value={rhymeMode} onChange={onRhymeModeChange} />
        <SaveStatusIndicator status={saveStatus} lastSavedAt={lastSavedAt} />
        <DraftPicker
          drafts={drafts}
          currentDraftId={currentDraftId}
          onSelect={onSelectDraft}
          onNew={onNewDraft}
          onDelete={onDeleteDraft}
        />
        <SettingsMenu
          language={language}
          theme={theme}
          onThemeChange={onThemeChange}
          rhymeHighlights={rhymeHighlights}
          onRhymeHighlightsChange={onRhymeHighlightsChange}
          rhymeHighlightStyle={rhymeHighlightStyle}
          onRhymeHighlightStyleChange={onRhymeHighlightStyleChange}
          syllableCounts={syllableCounts}
          onSyllableCountsChange={onSyllableCountsChange}
        />
      </div>
    </header>
  );
}

const TITLE_CLASS =
  "block w-full truncate font-serif text-2xl font-semibold tracking-tight text-foreground sm:text-3xl";

interface EditableTitleProps {
  /** Truncated, defaulted title shown when not editing. */
  displayTitle: string;
  /** Untruncated first lyric line; the input's value while editing. */
  editableTitle: string;
  placeholder: string;
  editLabel: string;
  onCommit: (title: string) => void;
}

function EditableTitle({
  displayTitle,
  editableTitle,
  placeholder,
  editLabel,
  onCommit,
}: EditableTitleProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(editableTitle);
  const inputRef = useRef<HTMLInputElement>(null);
  const skipBlurRef = useRef(false);

  useEffect(() => {
    if (editing) inputRef.current?.select();
  }, [editing]);

  if (editing) {
    return (
      <input
        ref={inputRef}
        value={draft}
        placeholder={placeholder}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={() => {
          if (skipBlurRef.current) {
            skipBlurRef.current = false;
            return;
          }
          setEditing(false);
          if (draft.trim() !== editableTitle) onCommit(draft);
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            setEditing(false);
            if (draft.trim() !== editableTitle) onCommit(draft);
          } else if (e.key === "Escape") {
            e.preventDefault();
            skipBlurRef.current = true;
            setDraft(editableTitle);
            setEditing(false);
          }
        }}
        aria-label={editLabel}
        className={`${TITLE_CLASS} border-b border-dashed border-accent/50 bg-transparent outline-none`}
      />
    );
  }

  return (
    <button
      type="button"
      onClick={() => {
        setDraft(editableTitle);
        setEditing(true);
      }}
      aria-label={editLabel}
      className={`${TITLE_CLASS} cursor-text rounded-sm text-left transition-colors hover:text-accent`}
    >
      {displayTitle}
    </button>
  );
}
