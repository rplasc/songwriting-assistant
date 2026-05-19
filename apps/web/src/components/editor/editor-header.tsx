"use client";

import type { ClientRhymeMode } from "@/features/analysis/rhyme-modes";
import type { DraftSummary, SaveStatus } from "@/features/drafts/drafts-types";
import type { Language } from "@/features/language/language-types";
import { DraftPicker } from "./draft-picker";
import { LanguageSelector } from "./language-selector";
import { RhymeModeToggle } from "./rhyme-mode-toggle";
import { SaveButton } from "./save-button";
import { SaveStatusIndicator } from "./save-status";

interface EditorHeaderProps {
  rhymeMode: ClientRhymeMode;
  onRhymeModeChange: (mode: ClientRhymeMode) => void;
  language: Language;
  onLanguageChange: (lang: Language) => void;
  saveStatus: SaveStatus;
  lastSavedAt: Date | null;
  onSave: () => void;
  drafts: DraftSummary[];
  currentDraftId: string | null;
  onSelectDraft: (id: string) => void;
  onNewDraft: () => void;
}

export function EditorHeader({
  rhymeMode,
  onRhymeModeChange,
  language,
  onLanguageChange,
  saveStatus,
  lastSavedAt,
  onSave,
  drafts,
  currentDraftId,
  onSelectDraft,
  onNewDraft,
}: EditorHeaderProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 px-1 py-1">
      <div className="flex items-center gap-5">
        <LanguageSelector value={language} onChange={onLanguageChange} />
        <RhymeModeToggle value={rhymeMode} onChange={onRhymeModeChange} />
      </div>
      <div className="flex items-center gap-3.5">
        <SaveStatusIndicator status={saveStatus} lastSavedAt={lastSavedAt} />
        <SaveButton status={saveStatus} onSave={onSave} />
        <DraftPicker
          drafts={drafts}
          currentDraftId={currentDraftId}
          onSelect={onSelectDraft}
          onNew={onNewDraft}
        />
      </div>
    </div>
  );
}
