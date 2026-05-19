import { Injectable } from '@nestjs/common';
import { Language } from '../../common/enums/language.enum';
import { Draft } from '../draft.types';

export interface DraftPayload {
  id: string;
  title: string;
  content: string;
  language: Language;
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
      created_at: d.createdAt,
      updated_at: d.updatedAt,
    };
  }
}
