import { apiBaseUrl } from "@/lib/config";
import type { Language } from "@/features/language/language-types";
import type { DraftSection } from "@/features/structure/structure-types";
import {
  toDraftAnalysis,
  type ServerDraftAnalysisPayload,
} from "./draft-analysis-mappers";
import type { DraftAnalysis } from "./draft-analysis-types";

export class DraftAnalysisRequestError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "DraftAnalysisRequestError";
  }
}

export interface AnalyzeDraftInput {
  draftId?: string | null;
  title?: string | null;
  content: string;
  language: Language;
  sections?: DraftSection[];
  forceRefresh?: boolean;
}

export interface AnalyzeDraftRequestOptions {
  signal?: AbortSignal;
}

export async function analyzeDraft(
  input: AnalyzeDraftInput,
  options: AnalyzeDraftRequestOptions = {},
): Promise<DraftAnalysis> {
  const body: Record<string, unknown> = {
    content: input.content,
    language: input.language,
  };
  if (input.draftId) body.draftId = input.draftId;
  if (input.title) body.title = input.title;
  if (input.sections && input.sections.length > 0) {
    body.sections = input.sections.map((s) => ({
      label: s.label,
      lineStart: s.lineStart,
      lineEnd: s.lineEnd,
    }));
  }
  if (input.forceRefresh) body.forceRefresh = true;

  const requestId =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const response = await fetch(`${apiBaseUrl}/v1/editor/analyze-draft`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-request-id": requestId,
    },
    body: JSON.stringify(body),
    signal: options.signal,
  });
  if (!response.ok) {
    throw new DraftAnalysisRequestError(
      `Draft analysis request failed (${response.status})`,
      response.status,
    );
  }
  const payload = (await response.json()) as ServerDraftAnalysisPayload;
  return toDraftAnalysis(payload);
}
