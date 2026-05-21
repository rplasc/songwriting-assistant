export interface StanzaRange {
  lineStart: number;
  lineEnd: number;
}

export interface DraftSection {
  id?: string;
  label: string;
  lineStart: number;
  lineEnd: number;
}

export interface ServerDraftSectionPayload {
  id: string;
  label: string;
  line_start: number;
  line_end: number;
}

export function sectionFromServer(p: ServerDraftSectionPayload): DraftSection {
  return {
    id: p.id,
    label: p.label,
    lineStart: p.line_start,
    lineEnd: p.line_end,
  };
}
