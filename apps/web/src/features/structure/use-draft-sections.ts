"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { Editor } from "@tiptap/react";
import { detectStanzasFromLines, stanzaKey } from "./stanza-detector";
import { getEditorLines } from "@/features/editor/tiptap/editor-lines";
import type { DraftSection, StanzaRange } from "./structure-types";

export interface UseDraftSectionsReturn {
  /** Detected stanzas in line order. */
  stanzas: StanzaRange[];
  /** Current labels keyed by stanza range; orphaned entries are dropped. */
  sections: DraftSection[];
  labelFor: (range: StanzaRange) => string | null;
  assignLabel: (range: StanzaRange, label: string) => void;
  clearLabel: (range: StanzaRange) => void;
  /** Hydrate labels when loading a draft from the server. */
  resetFromDraft: (sections: DraftSection[]) => void;
  /**
   * Labels that were previously applied but no longer match a detected
   * stanza (because lines shifted). Surface this via the margin notice so
   * the writer knows the gutter labels aren't silently lost.
   */
  droppedLabelCount: number;
  /** Purge orphaned labels from local state — used by the notice dismiss. */
  acknowledgeDroppedLabels: () => void;
}

function normalizeLabel(label: string): string {
  return label.trim().slice(0, 40);
}

/**
 * Reconcile stored labels against currently detected stanzas. Labels match
 * by exact (lineStart, lineEnd) — when content shifts and a stanza moves,
 * we drop the orphaned label rather than guess. The gutter menu re-applies
 * intentionally.
 */
function reconcile(
  stanzas: StanzaRange[],
  stored: Map<string, string>,
): DraftSection[] {
  const next: DraftSection[] = [];
  for (const range of stanzas) {
    const label = stored.get(stanzaKey(range));
    if (label) {
      next.push({ label, lineStart: range.lineStart, lineEnd: range.lineEnd });
    }
  }
  return next;
}

export function useDraftSections(editor: Editor | null): UseDraftSectionsReturn {
  const [stanzas, setStanzas] = useState<StanzaRange[]>([]);
  const [labels, setLabels] = useState<Map<string, string>>(() => new Map());

  useEffect(() => {
    if (!editor) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- clear local state when the editor detaches
      setStanzas((prev) => (prev.length === 0 ? prev : []));
      return;
    }
    const sync = () => setStanzas(detectStanzasFromLines(getEditorLines(editor)));
    sync();
    editor.on("update", sync);
    return () => {
      editor.off("update", sync);
    };
  }, [editor]);

  const sections = useMemo(() => reconcile(stanzas, labels), [stanzas, labels]);

  const droppedLabelCount = useMemo(() => {
    if (labels.size === 0) return 0;
    const keys = new Set(stanzas.map(stanzaKey));
    let count = 0;
    for (const k of labels.keys()) {
      if (!keys.has(k)) count += 1;
    }
    return count;
  }, [labels, stanzas]);

  const labelFor = useCallback(
    (range: StanzaRange): string | null =>
      labels.get(stanzaKey(range)) ?? null,
    [labels],
  );

  const assignLabel = useCallback((range: StanzaRange, label: string) => {
    const trimmed = normalizeLabel(label);
    setLabels((prev) => {
      const next = new Map(prev);
      if (!trimmed) {
        next.delete(stanzaKey(range));
      } else {
        next.set(stanzaKey(range), trimmed);
      }
      return next;
    });
  }, []);

  const clearLabel = useCallback((range: StanzaRange) => {
    setLabels((prev) => {
      if (!prev.has(stanzaKey(range))) return prev;
      const next = new Map(prev);
      next.delete(stanzaKey(range));
      return next;
    });
  }, []);

  const resetFromDraft = useCallback((next: DraftSection[]) => {
    const map = new Map<string, string>();
    for (const s of next) {
      map.set(`${s.lineStart}-${s.lineEnd}`, s.label);
    }
    setLabels(map);
  }, []);

  const acknowledgeDroppedLabels = useCallback(() => {
    setLabels((prev) => {
      if (prev.size === 0) return prev;
      const keys = new Set(stanzas.map(stanzaKey));
      let changed = false;
      const next = new Map<string, string>();
      for (const [k, v] of prev) {
        if (keys.has(k)) next.set(k, v);
        else changed = true;
      }
      return changed ? next : prev;
    });
  }, [stanzas]);

  return {
    stanzas,
    sections,
    labelFor,
    assignLabel,
    clearLabel,
    resetFromDraft,
    droppedLabelCount,
    acknowledgeDroppedLabels,
  };
}
