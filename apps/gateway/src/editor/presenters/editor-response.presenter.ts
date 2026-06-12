import { Injectable } from '@nestjs/common';
import {
  CapabilityReasonCode,
  CapabilityStatus,
} from '../../common/enums/capability.enum';
import {
  AdvancedRhymeMode,
  Language,
  RhymeMode,
  RhymeTargetType,
} from '../../common/enums/language.enum';
import {
  EvidenceTag,
  InnerRhymeGroup,
  LineAnalysisResponse,
  RhymeConfidence,
  RhymeFamily,
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
  inner_rhymes: InnerRhymeGroup[];
  meta: {
    request_id?: string;
    latency_ms: number;
  };
}

export interface ExploreRhymeItem {
  id: string;
  word: string;
  syllables: number;
  rhyme_type: string;
  rhyme_family: RhymeFamily | null;
  confidence: RhymeConfidence;
  evidence_tags: EvidenceTag[];
  matched_span: string | null;
  match_reason: string | null;
  score: number;
}

export interface ExploreRhymesPayload {
  query: string;
  target_type: RhymeTargetType;
  mode: AdvancedRhymeMode;
  language: Language;
  pronunciations_found: boolean;
  items: ExploreRhymeItem[];
  summary: {
    family_counts: Record<string, number>;
    returned: number;
    requested_limit: number;
  };
  capabilities: {
    multisyllabic: {
      status: CapabilityStatus;
      reason_code: CapabilityReasonCode | null;
    };
  };
  meta: {
    request_id?: string;
    latency_ms: number;
  };
}

interface ExploreContext {
  query: string;
  targetType: RhymeTargetType;
  mode: AdvancedRhymeMode;
  language: Language;
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
    targetWord?: string | null,
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
        // Echo the word that was actually rhymed (caret word or last-word
        // fallback) so the client can correlate replies.
        target_word: targetWord ?? line.last_word?.normalized ?? null,
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
      inner_rhymes: line.inner_rhymes ?? [],
      meta: {
        request_id: requestId,
        latency_ms: Math.round(latencyMs),
      },
    };
  }

  toExplorePayload(
    upstream: RhymeResponse,
    context: ExploreContext,
    latencyMs: number,
    requestId?: string,
  ): ExploreRhymesPayload {
    const multi = upstream.capabilities?.multisyllabic;
    return {
      query: upstream.query ?? context.query,
      // Echo the resolved values FastAPI applied so the client can react to
      // mode coercion (e.g. phrase-ending auto-upgrade to multisyllabic).
      target_type: upstream.target_type ?? context.targetType,
      mode: (upstream.mode as AdvancedRhymeMode | undefined) ?? context.mode,
      language: upstream.language ?? context.language,
      pronunciations_found: upstream.pronunciations_found,
      items: (upstream.rhymes ?? []).map((r, i) => ({
        // FastAPI is supposed to assign an id; preserve any client-visible
        // ordering when it doesn't so React keys stay stable across reorders.
        id: r.id && r.id.length > 0 ? r.id : `${r.word}-${i}`,
        word: r.word,
        syllables: r.syllables,
        rhyme_type: r.rhyme_type,
        rhyme_family: r.rhyme_family ?? null,
        confidence: r.confidence ?? 'low',
        evidence_tags: r.evidence_tags ?? [],
        matched_span: r.matched_span ?? null,
        match_reason: r.match_reason ?? null,
        score: r.score,
      })),
      summary: {
        family_counts: upstream.summary?.family_counts ?? {},
        returned: upstream.summary?.returned ?? upstream.rhymes?.length ?? 0,
        requested_limit: upstream.summary?.requested_limit ?? 0,
      },
      capabilities: {
        multisyllabic: {
          status: multi?.status ?? 'full',
          reason_code: multi?.reason_code ?? null,
        },
      },
      meta: {
        request_id: requestId,
        latency_ms: Math.round(latencyMs),
      },
    };
  }
}
