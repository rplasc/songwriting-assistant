import { Injectable, NotFoundException } from '@nestjs/common';
import { randomUUID } from 'crypto';
import { Draft } from './draft.types';

const DEFAULT_TITLE = 'Untitled Draft';

@Injectable()
export class DraftsService {
  private readonly drafts = new Map<string, Draft>();

  create(input: { title?: string; content: string }): Draft {
    const now = new Date().toISOString();
    const draft: Draft = {
      id: randomUUID(),
      title: input.title?.length ? input.title : DEFAULT_TITLE,
      content: input.content,
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

  update(id: string, patch: { title?: string; content?: string }): Draft {
    const existing = this.findById(id);
    const updated: Draft = {
      ...existing,
      title: patch.title !== undefined ? patch.title : existing.title,
      content: patch.content !== undefined ? patch.content : existing.content,
      updatedAt: new Date().toISOString(),
    };
    this.drafts.set(id, updated);
    return updated;
  }
}
