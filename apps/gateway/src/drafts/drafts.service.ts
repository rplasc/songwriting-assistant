import {
  BadRequestException,
  ConflictException,
  Injectable,
  Logger,
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
  /**
   * If supplied, the update only succeeds when this matches the stored
   * draft's current version. Omit to keep last-write-wins (back-compat
   * with clients that do not send If-Match yet).
   */
  expectedVersion?: number;
}

export interface OperationContext {
  requestId?: string;
}

@Injectable()
export class DraftsService {
  private readonly logger = new Logger(DraftsService.name);
  private readonly drafts = new Map<string, Draft>();

  create(input: CreateDraftInput, ctx: OperationContext = {}): Draft {
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
      version: 1,
      createdAt: now,
      updatedAt: now,
    };
    this.drafts.set(draft.id, draft);
    this.logOp('draft.create', ctx, {
      draftId: draft.id,
      version: draft.version,
      contentChars: draft.content.length,
      sectionCount: draft.sections?.length ?? 0,
    });
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

  update(
    id: string,
    patch: UpdateDraftInput,
    ctx: OperationContext = {},
  ): Draft {
    const existing = this.findById(id);
    if (
      patch.expectedVersion !== undefined &&
      patch.expectedVersion !== existing.version
    ) {
      throw new ConflictException({
        code: 'DRAFT_VERSION_CONFLICT',
        message: `Draft ${id} has been modified (expected version ${patch.expectedVersion}, current ${existing.version}).`,
        currentVersion: existing.version,
      });
    }
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
      version: existing.version + 1,
      updatedAt: new Date().toISOString(),
    };
    this.drafts.set(id, updated);
    this.logOp('draft.update', ctx, {
      draftId: id,
      versionFrom: existing.version,
      versionTo: updated.version,
      contentChars: updated.content.length,
      sectionCount: updated.sections?.length ?? 0,
    });
    return updated;
  }

  remove(id: string, ctx: OperationContext = {}): void {
    const existing = this.drafts.get(id);
    if (!existing) {
      throw new NotFoundException({
        code: 'DRAFT_NOT_FOUND',
        message: `Draft ${id} not found`,
      });
    }
    this.drafts.delete(id);
    this.logOp('draft.remove', ctx, {
      draftId: id,
      version: existing.version,
    });
  }

  private logOp(
    event: string,
    ctx: OperationContext,
    fields: Record<string, unknown>,
  ): void {
    const parts = [event, `request_id=${ctx.requestId ?? '-'}`];
    for (const [k, v] of Object.entries(fields)) {
      parts.push(`${k}=${String(v)}`);
    }
    this.logger.log(parts.join(' '));
  }

  private countContentLines(content: string): number {
    if (content.length === 0) return 0;
    // HTML content (TipTap getHTML): count paragraph closing tags, since
    // paragraphs aren't separated by newlines in the serialized output.
    if (content.trimStart().startsWith('<')) {
      return (content.match(/<\/p>/gi) ?? []).length;
    }
    return content.split('\n').length;
  }

  private normalizeSections(
    inputs: SectionInput[],
    content: string,
  ): DraftSection[] {
    const lineCount = this.countContentLines(content);
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
