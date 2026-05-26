import { Injectable } from '@nestjs/common';
import { createHash, randomUUID } from 'crypto';
import {
  AnalysisMode,
  DEFAULT_ANALYSIS_MODE,
} from '../../common/enums/analysis-mode.enum';
import {
  DEFAULT_LANGUAGE,
  Language,
} from '../../common/enums/language.enum';
import { DraftSection } from '../../drafts/draft.types';
import {
  AnalyzeDraftSection,
  AnalyzeDraftUpstreamOptions,
} from '../../fastapi/dto/fastapi-requests';
import { AnalyzeDraftOptionsDto } from '../dto/analyze-draft-options.dto';

export interface ResolvedDraftAnalysisRequest {
  language: Language;
  analysisMode: AnalysisMode;
  sections: DraftSection[];
  revisionHash: string;
  upstreamSections: AnalyzeDraftSection[];
  upstreamOptions: AnalyzeDraftUpstreamOptions | undefined;
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
    analysisMode?: AnalysisMode;
    options?: AnalyzeDraftOptionsDto;
    inlineSections?: Array<{
      label: string;
      lineStart: number;
      lineEnd: number;
    }>;
    storedSections?: DraftSection[];
  }): ResolvedDraftAnalysisRequest {
    const language = input.language ?? DEFAULT_LANGUAGE;
    const analysisMode = input.analysisMode ?? DEFAULT_ANALYSIS_MODE;

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

    // Standard mode ignores advanced options; only revision_review forwards them.
    const upstreamOptions =
      analysisMode === 'revision_review'
        ? this.toUpstreamOptions(input.options)
        : undefined;

    return {
      language,
      analysisMode,
      sections,
      revisionHash,
      upstreamSections,
      upstreamOptions,
    };
  }

  private toUpstreamOptions(
    opts: AnalyzeDraftOptionsDto | undefined,
  ): AnalyzeDraftUpstreamOptions | undefined {
    if (!opts) return undefined;
    const out: AnalyzeDraftUpstreamOptions = {};
    if (opts.includeSemanticRepetition !== undefined)
      out.include_semantic_repetition = opts.includeSemanticRepetition;
    if (opts.includeMotifTracking !== undefined)
      out.include_motif_tracking = opts.includeMotifTracking;
    if (opts.includeSectionContrast !== undefined)
      out.include_section_contrast = opts.includeSectionContrast;
    if (opts.includeConsistencyHints !== undefined)
      out.include_consistency_hints = opts.includeConsistencyHints;
    return Object.keys(out).length > 0 ? out : undefined;
  }
}
