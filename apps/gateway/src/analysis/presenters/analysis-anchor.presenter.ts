import { Injectable } from '@nestjs/common';
import { AnchorScope } from '../../common/enums/capability.enum';
import { UpstreamInsightAnchor } from '../../fastapi/dto/fastapi-responses';

export interface AnalysisAnchorPayload {
  scope: AnchorScope;
  section_id: string | null;
  line_start: number | null;
  line_end: number | null;
}

@Injectable()
export class AnalysisAnchorPresenter {
  toClient(input: UpstreamInsightAnchor | null): AnalysisAnchorPayload | null {
    if (!input) return null;
    return {
      scope: input.scope,
      section_id: input.section_id,
      line_start: input.line_start,
      line_end: input.line_end,
    };
  }
}
