import { Injectable } from '@nestjs/common';
import { Language, RhymeMode } from '../../common/enums/language.enum';
import {
  LineAnalysisResponse,
  RhymeResponse,
} from '../../fastapi/dto/fastapi-responses';

export interface EditorAnalysisPayload {
  line: string;
  language: Language;
  syllables: {
    total: number;
    tokens: { text: string; syllables: number; low_confidence?: boolean }[];
  };
  rhymes: {
    target_word: string | null;
    mode: RhymeMode;
    items: { word: string; syllables: number; type: string }[];
  };
  meta: {
    request_id?: string;
    latency_ms: number;
  };
}

@Injectable()
export class EditorResponsePresenter {
  toClient(
    line: LineAnalysisResponse,
    rhymes: RhymeResponse | null,
    latencyMs: number,
    mode: RhymeMode,
    language: Language,
    requestId?: string,
  ): EditorAnalysisPayload {
    return {
      line: line.line,
      language,
      syllables: {
        total: line.total_syllables,
        tokens: line.tokens.map((t) => ({
          text: t.text,
          syllables: t.syllables,
          low_confidence: t.low_confidence ?? false,
        })),
      },
      rhymes: {
        target_word: line.last_word?.normalized ?? null,
        // If FastAPI returned a resolved mode in its meta, prefer it so the
        // echoed value reflects exactly what produced these candidates.
        mode: (rhymes?.meta?.mode as RhymeMode | undefined) ?? mode,
        items:
          rhymes?.rhymes.map((r) => ({
            word: r.word,
            syllables: r.syllables,
            type: r.rhyme_type,
          })) ?? [],
      },
      meta: {
        request_id: requestId,
        latency_ms: Math.round(latencyMs),
      },
    };
  }
}
