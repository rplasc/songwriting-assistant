import { apiBaseUrl } from "@/lib/config";
import type { Language } from "@/features/language/language-types";
import { toInsight } from "@/features/draft-analysis/draft-analysis-mappers";
import type { CapabilityLevel } from "@/features/draft-analysis/draft-analysis-types";
import type {
  CompareCapabilities,
  CompareSummary,
  DraftCompareResult,
} from "./draft-compare-types";

export class DraftCompareRequestError extends Error {
  constructor(
    message: string,
    readonly status?: number,
    /** Server-supplied error code, e.g. COMPARE_BASELINE_UNAVAILABLE. */
    readonly code?: string,
  ) {
    super(message);
    this.name = "DraftCompareRequestError";
  }
}

/** Gateway error code for an evicted / unknown snapshot revision. */
export const COMPARE_BASELINE_UNAVAILABLE_CODE = "COMPARE_BASELINE_UNAVAILABLE";

export interface AnalyzeDraftCompareInput {
  draftId: string;
  baseRevisionHash: string;
  targetRevisionHash: string;
  language?: Language;
  title?: string | null;
}

export interface AnalyzeDraftCompareOptions {
  signal?: AbortSignal;
}

interface ServerCapability {
  status: CapabilityLevel;
  reason_code: string | null;
}

interface ServerCompareSummary {
  motif_delta_count: number;
  repetition_delta_count: number;
  section_delta_count: number;
  consistency_delta_count: number;
  family_counts: Record<string, number>;
  unmatched_previous_section_ids: string[];
  unmatched_current_section_ids: string[];
}

interface ServerCompareCapabilities {
  compare_motifs: ServerCapability;
  compare_repetition: ServerCapability;
  compare_sections: ServerCapability;
  compare_consistency: ServerCapability;
}

interface ServerComparePayload {
  analysis_id: string;
  draft_id: string | null;
  language: Language;
  title: string | null;
  previous: { revision_hash: string };
  current: { revision_hash: string };
  summary: ServerCompareSummary;
  insights: Parameters<typeof toInsight>[0][];
  capabilities: ServerCompareCapabilities;
  meta: { request_id?: string; latency_ms: number };
}

function toSummary(s: ServerCompareSummary): CompareSummary {
  return {
    motifDeltaCount: s.motif_delta_count,
    repetitionDeltaCount: s.repetition_delta_count,
    sectionDeltaCount: s.section_delta_count,
    consistencyDeltaCount: s.consistency_delta_count,
    familyCounts: s.family_counts ?? {},
    unmatchedPreviousSectionIds: s.unmatched_previous_section_ids ?? [],
    unmatchedCurrentSectionIds: s.unmatched_current_section_ids ?? [],
  };
}

function toCapabilities(s: ServerCompareCapabilities): CompareCapabilities {
  return {
    compareMotifs: s.compare_motifs.status,
    compareRepetition: s.compare_repetition.status,
    compareSections: s.compare_sections.status,
    compareConsistency: s.compare_consistency.status,
  };
}

export async function analyzeDraftCompare(
  input: AnalyzeDraftCompareInput,
  options: AnalyzeDraftCompareOptions = {},
): Promise<DraftCompareResult> {
  const body: Record<string, unknown> = {
    draftId: input.draftId,
    baseRevisionHash: input.baseRevisionHash,
    targetRevisionHash: input.targetRevisionHash,
  };
  if (input.language) body.language = input.language;
  if (input.title) body.title = input.title;

  const requestId =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

  const response = await fetch(
    `${apiBaseUrl}/v1/editor/analyze-draft-compare`,
    {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-request-id": requestId,
      },
      body: JSON.stringify(body),
      signal: options.signal,
    },
  );

  if (!response.ok) {
    // Try to surface the gateway's typed error envelope so the hook can
    // distinguish snapshot-eviction (recoverable, prompt user to re-baseline)
    // from generic failures.
    let code: string | undefined;
    let message = `Draft compare request failed (${response.status})`;
    try {
      const body = (await response.json()) as
        | { message?: unknown; code?: unknown }
        | undefined;
      if (body && typeof body === "object") {
        if (typeof body.code === "string") code = body.code;
        if (typeof body.message === "string") message = body.message;
      }
    } catch {
      // Non-JSON body — keep generic message.
    }
    throw new DraftCompareRequestError(message, response.status, code);
  }

  const payload = (await response.json()) as ServerComparePayload;
  return {
    analysisId: payload.analysis_id,
    draftId: payload.draft_id,
    language: payload.language,
    title: payload.title,
    baseRevisionHash: payload.previous.revision_hash,
    targetRevisionHash: payload.current.revision_hash,
    summary: toSummary(payload.summary),
    insights: (payload.insights ?? []).map(toInsight),
    capabilities: toCapabilities(payload.capabilities),
    latencyMs: payload.meta?.latency_ms ?? 0,
  };
}
