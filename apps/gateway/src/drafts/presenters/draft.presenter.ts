import { Injectable } from '@nestjs/common';
import { Language } from '../../common/enums/language.enum';
import { Draft, DraftSection } from '../draft.types';

export interface DraftSectionPayload {
  id: string;
  label: string;
  line_start: number;
  line_end: number;
}

export interface DraftPayload {
  id: string;
  title: string;
  content: string;
  language: Language;
  sections: DraftSectionPayload[];
  version: number;
  created_at: string;
  updated_at: string;
}

@Injectable()
export class DraftPresenter {
  toClient(d: Draft): DraftPayload {
    return {
      id: d.id,
      title: d.title,
      content: d.content,
      language: d.language,
      sections: (d.sections ?? []).map((s) => this.toSectionPayload(s)),
      version: d.version,
      created_at: d.createdAt,
      updated_at: d.updatedAt,
    };
  }

  toSectionPayload(s: DraftSection): DraftSectionPayload {
    return {
      id: s.id,
      label: s.label,
      line_start: s.lineStart,
      line_end: s.lineEnd,
    };
  }
}
