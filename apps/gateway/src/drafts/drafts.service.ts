import { Injectable, NotFoundException } from '@nestjs/common';
import { randomUUID } from 'crypto';
import { DEFAULT_LANGUAGE, Language } from '../common/enums/language.enum';
import { Draft } from './draft.types';

const DEFAULT_TITLE = 'Untitled Draft';

export interface CreateDraftInput {
  title?: string;
  content: string;
  language?: Language;
}

export interface UpdateDraftInput {
  title?: string;
  content?: string;
  language?: Language;
}

@Injectable()
export class DraftsService {
  private readonly drafts = new Map<string, Draft>();

  create(input: CreateDraftInput): Draft {
    const now = new Date().toISOString();
    const draft: Draft = {
      id: randomUUID(),
      title: input.title?.length ? input.title : DEFAULT_TITLE,
      content: input.content,
      language: input.language ?? DEFAULT_LANGUAGE,
      createdAt: now,
      updatedAt: now,
    };
    this.drafts.set(draft.id, draft);
    return draft;
  }

  findById(id: string): Draft {
    const draft = this.drafts.get(id);
    if (!draft) {
      throw new NotFoundException({
        code: 'DRAFT_NOT_FOUND',
        message: `Draft ${id} not found`,
      });
    }
    return draft;
  }

  update(id: string, patch: UpdateDraftInput): Draft {
    const existing = this.findById(id);
    const updated: Draft = {
      ...existing,
      title: patch.title !== undefined ? patch.title : existing.title,
      content: patch.content !== undefined ? patch.content : existing.content,
      language:
        patch.language !== undefined ? patch.language : existing.language,
      updatedAt: new Date().toISOString(),
    };
    this.drafts.set(id, updated);
    return updated;
  }
}
