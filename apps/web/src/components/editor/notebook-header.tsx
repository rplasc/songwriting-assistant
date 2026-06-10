"use client";

import type { ClientRhymeMode } from "@/features/analysis/rhyme-modes";
import type { DraftSummary, SaveStatus } from "@/features/drafts/drafts-types";
import { deriveTitle } from "@/features/drafts/derive-title";
import type { Language } from "@/features/language/language-types";
import { DraftPicker } from "./draft-picker";
import { LanguageSelector } from "./language-selector";
import { RhymeModeToggle } from "./rhyme-mode-toggle";
import { SaveStatusIndicator } from "./save-status";

const SUBTITLE: Record<Language, string> = {
  en: "A studio notebook — words first, counts in the margin.",
  es: "Un cuaderno de estudio — primero las palabras, las cuentas al margen.",
};

interface NotebookHeaderProps {
  content: string;
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
}

export function NotebookHeader({
  content,
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
}: NotebookHeaderProps) {
  return (
    <header className="flex flex-wrap items-start justify-between gap-x-8 gap-y-4">
      <div className="min-w-0">
        <h1 className="truncate font-serif text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
          {deriveTitle(content)}
        </h1>
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
      </div>
    </header>
  );
}
