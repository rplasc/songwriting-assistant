import {
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { randomUUID } from 'crypto';
import { DEFAULT_LANGUAGE, Language } from '../common/enums/language.enum';
import { Draft, DraftSection } from './draft.types';

const DEFAULT_TITLE = 'Untitled Draft';

export interface SectionInput {
  label: string;
  lineStart: number;
  lineEnd: number;
}

export interface CreateDraftInput {
  title?: string;
  content: string;
  language?: Language;
  sections?: SectionInput[];
}

export interface UpdateDraftInput {
  title?: string;
  content?: string;
  language?: Language;
  sections?: SectionInput[];
}

@Injectable()
export class DraftsService {
  private readonly drafts = new Map<string, Draft>();

  create(input: CreateDraftInput): Draft {
    const now = new Date().toISOString();
    const sections =
      input.sections !== undefined
        ? this.normalizeSections(input.sections, input.content)
        : undefined;
    const draft: Draft = {
      id: randomUUID(),
      title: input.title?.length ? input.title : DEFAULT_TITLE,
      content: input.content,
      language: input.language ?? DEFAULT_LANGUAGE,
      sections,
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
    const nextContent =
      patch.content !== undefined ? patch.content : existing.content;
    const nextSections =
      patch.sections !== undefined
        ? this.normalizeSections(patch.sections, nextContent)
        : existing.sections;
    const updated: Draft = {
      ...existing,
      title: patch.title !== undefined ? patch.title : existing.title,
      content: nextContent,
      language:
        patch.language !== undefined ? patch.language : existing.language,
      sections: nextSections,
      updatedAt: new Date().toISOString(),
    };
    this.drafts.set(id, updated);
    return updated;
  }

  remove(id: string): void {
    if (!this.drafts.delete(id)) {
      throw new NotFoundException({
        code: 'DRAFT_NOT_FOUND',
        message: `Draft ${id} not found`,
      });
    }
  }

  private normalizeSections(
    inputs: SectionInput[],
    content: string,
  ): DraftSection[] {
    const lineCount = content.length === 0 ? 0 : content.split('\n').length;
    const sorted = [...inputs].sort((a, b) => a.lineStart - b.lineStart);
    let prevEnd = 0;
    for (const s of sorted) {
      if (s.lineStart > s.lineEnd) {
        throw new BadRequestException({
          code: 'INVALID_SECTIONS',
          message: `Section "${s.label}" has lineStart (${s.lineStart}) greater than lineEnd (${s.lineEnd}).`,
        });
      }
      if (s.lineEnd > lineCount) {
        throw new BadRequestException({
          code: 'INVALID_SECTIONS',
          message: `Section "${s.label}" lineEnd (${s.lineEnd}) exceeds content line count (${lineCount}).`,
        });
      }
      if (s.lineStart <= prevEnd) {
        throw new BadRequestException({
          code: 'INVALID_SECTIONS',
          message: `Sections overlap at line ${s.lineStart}.`,
        });
      }
      prevEnd = s.lineEnd;
    }
    return sorted.map((s) => ({
      id: randomUUID(),
      label: s.label,
      lineStart: s.lineStart,
      lineEnd: s.lineEnd,
    }));
  }
}
