import { Injectable } from '@nestjs/common';
import {
  LineAnalysisResponse,
  RhymeResponse,
} from '../../fastapi/dto/fastapi-responses';
import { RhymeMode } from '../dto/analyze-line.dto';

export interface EditorAnalysisPayload {
  line: string;
  syllables: {
    total: number;
    tokens: { text: string; syllables: number }[];
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
    requestId?: string,
  ): EditorAnalysisPayload {
    return {
      line: line.line,
      syllables: {
        total: line.total_syllables,
        tokens: line.tokens.map((t) => ({
          text: t.text,
          syllables: t.syllables,
        })),
      },
      rhymes: {
        target_word: line.last_word?.normalized ?? null,
        mode,
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
