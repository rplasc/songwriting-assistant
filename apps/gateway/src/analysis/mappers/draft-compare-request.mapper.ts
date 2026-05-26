import { Injectable } from '@nestjs/common';
import { DEFAULT_LANGUAGE, Language } from '../../common/enums/language.enum';
import { DraftSnapshot } from '../../drafts/snapshot.types';
import {
  AnalyzeDraftCompareRequest,
  AnalyzeDraftSection,
  DraftCompareUpstreamOptions,
  DraftCompareUpstreamSide,
} from '../../fastapi/dto/fastapi-requests';
import { AnalyzeDraftCompareOptionsDto } from '../dto/analyze-draft-compare-options.dto';

@Injectable()
export class DraftCompareRequestMapper {
  resolve(input: {
    language?: Language;
    title?: string;
    base: DraftSnapshot;
    target: DraftSnapshot;
    options?: AnalyzeDraftCompareOptionsDto;
  }): AnalyzeDraftCompareRequest {
    return {
      language: input.language ?? DEFAULT_LANGUAGE,
      title: input.title,
      previous: this.toSide(input.base),
      current: this.toSide(input.target),
      options: this.toUpstreamOptions(input.options),
    };
  }

  private toSide(snapshot: DraftSnapshot): DraftCompareUpstreamSide {
    const sections: AnalyzeDraftSection[] = snapshot.sections.map((s) => ({
      id: s.id,
      label: s.label,
      line_start: s.lineStart,
      line_end: s.lineEnd,
    }));
    return {
      content: snapshot.content,
      sections: sections.length > 0 ? sections : undefined,
    };
  }

  private toUpstreamOptions(
    opts: AnalyzeDraftCompareOptionsDto | undefined,
  ): DraftCompareUpstreamOptions | undefined {
    if (!opts) return undefined;
    const out: DraftCompareUpstreamOptions = {};
    if (opts.compareMotifs !== undefined) out.compare_motifs = opts.compareMotifs;
    if (opts.compareRepetition !== undefined)
      out.compare_repetition = opts.compareRepetition;
    if (opts.compareSections !== undefined)
      out.compare_sections = opts.compareSections;
    if (opts.compareConsistency !== undefined)
      out.compare_consistency = opts.compareConsistency;
    return Object.keys(out).length > 0 ? out : undefined;
  }
}
