import { apiBaseUrl } from "@/lib/config";
import type { Language } from "@/features/language/language-types";
import type {
  AdvancedRhymeItem,
  AdvancedRhymeMode,
  AdvancedRhymeResult,
  AdvancedRhymeTargetType,
  CapabilityReasonCode,
  EvidenceTag,
  RhymeConfidence,
  RhymeFamily,
} from "./advanced-rhyme-types";

export class AdvancedRhymeRequestError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "AdvancedRhymeRequestError";
  }
}

export interface ExploreRhymesInput {
  query: string;
  targetType: AdvancedRhymeTargetType;
  mode: AdvancedRhymeMode;
  language: Language;
  limit?: number;
}

export interface ExploreRhymesOptions {
  signal?: AbortSignal;
}

interface ServerExploreItem {
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

interface ServerExplorePayload {
  query: string;
  target_type: AdvancedRhymeTargetType;
  mode: AdvancedRhymeMode;
  language: Language;
  pronunciations_found: boolean;
  items: ServerExploreItem[];
  summary: {
    family_counts: Record<string, number>;
    returned: number;
    requested_limit: number;
  };
  capabilities: {
    multisyllabic: {
      status: "full" | "partial" | "unsupported";
      reason_code: CapabilityReasonCode | null;
    };
  };
  meta: { request_id?: string; latency_ms: number };
}

function toItem(s: ServerExploreItem): AdvancedRhymeItem {
  return {
    id: s.id,
    word: s.word,
    syllables: s.syllables,
    rhymeType: s.rhyme_type,
    rhymeFamily: s.rhyme_family,
    confidence: s.confidence,
    evidenceTags: s.evidence_tags ?? [],
    matchedSpan: s.matched_span,
    matchReason: s.match_reason,
    score: s.score,
  };
}

export async function exploreRhymes(
  input: ExploreRhymesInput,
  options: ExploreRhymesOptions = {},
): Promise<AdvancedRhymeResult> {
  const body: Record<string, unknown> = {
    query: input.query,
    target_type: input.targetType,
    mode: input.mode,
    language: input.language,
  };
  if (typeof input.limit === "number") body.limit = input.limit;

  const requestId =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

  const response = await fetch(`${apiBaseUrl}/v1/editor/rhymes/explore`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-request-id": requestId,
    },
    body: JSON.stringify(body),
    signal: options.signal,
  });

  if (!response.ok) {
    throw new AdvancedRhymeRequestError(
      `Advanced rhyme request failed (${response.status})`,
      response.status,
    );
  }

  const payload = (await response.json()) as ServerExplorePayload;
  return {
    query: payload.query,
    targetType: payload.target_type,
    mode: payload.mode,
    language: payload.language,
    pronunciationsFound: payload.pronunciations_found,
    items: payload.items.map(toItem),
    familyCounts: payload.summary?.family_counts ?? {},
    capabilities: {
      multisyllabic: {
        status: payload.capabilities.multisyllabic.status,
        reasonCode: payload.capabilities.multisyllabic.reason_code,
      },
    },
    latencyMs: payload.meta?.latency_ms ?? 0,
  };
}
