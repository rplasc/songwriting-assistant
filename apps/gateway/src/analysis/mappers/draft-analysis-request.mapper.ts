import { Injectable } from '@nestjs/common';
import { createHash, randomUUID } from 'crypto';
import {
  DEFAULT_LANGUAGE,
  Language,
} from '../../common/enums/language.enum';
import { DraftSection } from '../../drafts/draft.types';
import { AnalyzeDraftSection } from '../../fastapi/dto/fastapi-requests';

export interface ResolvedDraftAnalysisRequest {
  language: Language;
  sections: DraftSection[];
  revisionHash: string;
  upstreamSections: AnalyzeDraftSection[];
}

/**
 * Resolves draft-analysis request inputs into a normalized shape that the
 * service can forward to FastAPI without duplicating defaulting or hashing
 * logic in multiple places.
 */
@Injectable()
export class DraftAnalysisRequestMapper {
  resolve(input: {
    content: string;
    language?: Language;
    inlineSections?: Array<{
      label: string;
      lineStart: number;
      lineEnd: number;
    }>;
    storedSections?: DraftSection[];
  }): ResolvedDraftAnalysisRequest {
    const language = input.language ?? DEFAULT_LANGUAGE;

    let sections: DraftSection[];
    if (input.inlineSections !== undefined) {
      sections = input.inlineSections.map((s) => ({
        id: randomUUID(),
        label: s.label,
        lineStart: s.lineStart,
        lineEnd: s.lineEnd,
      }));
    } else if (input.storedSections !== undefined) {
      sections = input.storedSections;
    } else {
      sections = [];
    }

    const revisionHash = createHash('sha256')
      .update(input.content)
      .digest('hex')
      .slice(0, 16);

    const upstreamSections: AnalyzeDraftSection[] = sections.map((s) => ({
      id: s.id,
      label: s.label,
      line_start: s.lineStart,
      line_end: s.lineEnd,
    }));

    return { language, sections, revisionHash, upstreamSections };
  }
}
